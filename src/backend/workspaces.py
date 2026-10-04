"""Workspace services for document analysis and judgment search."""
from __future__ import annotations

import io
import re
from dataclasses import asdict
from typing import Any

from pypdf import PdfReader

from generation.groq import GroqGenerator
from retrieval.bm25 import BM25Retriever
from retrieval.dense import DenseRetriever
from retrieval.rrf import reciprocal_rank_fusion

_SOURCE_RE = re.compile(r"\[SOURCE:\s*([^\]]+)\]")


class WorkspaceService:
    def __init__(
        self,
        bm25_index="data/indexes/bm25",
        dense_index="data/indexes/faiss",
        embedding_model="BAAI/bge-small-en-v1.5",
        device="cpu",
        cache_dir=".modal_cache",
        generator: GroqGenerator | None = None,
    ) -> None:
        self.bm25 = BM25Retriever(bm25_index)
        self.dense = DenseRetriever(dense_index, embedding_model, device, cache_dir)
        self.generator = generator or GroqGenerator(max_chunks=8, max_context_chars=12000)

    def search_case_law(self, query: str, top_k: int = 8) -> list[dict[str, Any]]:
        if not query.strip():
            raise ValueError("query must not be empty")
        if top_k <= 0:
            raise ValueError("top_k must be greater than zero")
        k = max(50, top_k * 5)
        bm25 = [r for r in self.bm25.retrieve(query, k) if r.doc_id.startswith("judgment:")]
        dense = [r for r in self.dense.retrieve(query, k) if r.doc_id.startswith("judgment:")]
        fused = reciprocal_rank_fusion(bm25, dense, 60, top_k)
        return [asdict(item) for item in fused]

    @staticmethod
    def _extract_pdf(content: bytes) -> tuple[int, list[str]]:
        try:
            reader = PdfReader(io.BytesIO(content))
            pages = [(page.extract_text() or "").strip() for page in reader.pages]
        except Exception as exc:
            raise ValueError(f"Could not read the uploaded PDF: {exc}") from exc
        nonempty = [(i + 1, text) for i, text in enumerate(pages) if text]
        if not nonempty:
            raise ValueError("The PDF contains no extractable text. Scanned PDFs need OCR first.")
        return len(pages), [f"[Page {page}]\n{text}" for page, text in nonempty]

    def analyze_document(self, filename: str, content: bytes, instruction: str) -> dict[str, Any]:
        if not filename.lower().endswith(".pdf"):
            raise ValueError("Only PDF documents are supported.")
        if len(content) > 20 * 1024 * 1024:
            raise ValueError("The uploaded PDF exceeds the 20 MB limit.")
        if not instruction.strip():
            raise ValueError("instruction must not be empty")

        pages, blocks = self._extract_pdf(content)
        prompt = (
            f"{instruction.strip()}\n\n"
            "This is a temporary uploaded legal document. Use only the supplied pages. "
            "Cite every material claim with the page source marker, for example "
            "[SOURCE: Page 3]. If the document does not support a claim, say so."
        )
        generated = self.generator.generate_with_context(prompt, blocks, source_prefix="SOURCE")
        cited = _SOURCE_RE.findall(generated.answer)
        sources = []
        by_page = {i + 1: text for i, text in enumerate([b.split("\n", 1)[-1] for b in blocks])}
        for source in cited:
            match = re.fullmatch(r"Page\s+(\d+)", source.strip(), re.IGNORECASE)
            if match:
                page = int(match.group(1))
                if page in by_page:
                    sources.append({"chunk_id": f"page:{page}", "text": by_page[page], "metadata": {"page": page}})
        return {
            "filename": filename,
            "pages": pages,
            "model": generated.model,
            "answer": generated.answer,
            "citations": cited,
            "sources": sources,
        }
