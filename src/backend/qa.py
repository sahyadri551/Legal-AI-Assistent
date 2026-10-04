"""End-to-end hybrid retrieval and grounded generation service."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from generation.groq import GenerationResult, GroqGenerator
from retrieval.bm25 import BM25Retriever
from retrieval.dense import DenseRetriever
from retrieval.rrf import RRFResult, reciprocal_rank_fusion


@dataclass(frozen=True)
class QAResult:
    generation: GenerationResult
    retrieved: list[RRFResult]


class HybridQAService:
    def __init__(
        self,
        bm25_index: Path = Path("data/indexes/bm25"),
        dense_index: Path = Path("data/indexes/faiss"),
        model: str = "BAAI/bge-small-en-v1.5",
        device: str = "cpu",
        cache_dir: Path = Path(".modal_cache"),
        retrieval_k: int = 50,
        rrf_k: int = 60,
        top_k: int = 8,
        generator: GroqGenerator | None = None,
    ) -> None:
        if retrieval_k <= 0 or rrf_k <= 0 or top_k <= 0:
            raise ValueError("retrieval_k, rrf_k, and top_k must be greater than zero")
        self.bm25 = BM25Retriever(bm25_index)
        self.dense = DenseRetriever(dense_index, model, device, cache_dir)
        self.rrf_k = rrf_k
        self.retrieval_k = retrieval_k
        self.top_k = top_k
        # Created lazily so retrieval/search works without a Groq API key.
        self._generator = generator

    @property
    def generator(self) -> GroqGenerator:
        if self._generator is None:
            self._generator = GroqGenerator()
        return self._generator

    @generator.setter
    def generator(self, value: GroqGenerator) -> None:
        self._generator = value

    def retrieve(self, query: str, top_k: int | None = None) -> list[RRFResult]:
        if not query.strip():
            raise ValueError("query must not be empty")
        fused = reciprocal_rank_fusion(
            self.bm25.retrieve(query, self.retrieval_k),
            self.dense.retrieve(query, self.retrieval_k),
            self.rrf_k,
            top_k or self.top_k,
        )
        return fused

    def answer_from_results(self, query: str, results: list[RRFResult]) -> QAResult:
        if not query.strip():
            raise ValueError("query must not be empty")
        generation = self.generator.generate(query, results)
        return QAResult(generation=generation, retrieved=results)

    def answer(self, query: str) -> QAResult:
        results = self.retrieve(query)
        return self.answer_from_results(query, results)
