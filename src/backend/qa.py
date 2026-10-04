"""End-to-end hybrid retrieval and grounded generation service."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from retrieval.bm25 import BM25Retriever
from retrieval.dense import DenseRetriever
from retrieval.rrf import RRFResult, reciprocal_rank_fusion
from generation.ollama import GenerationResult, OllamaGenerator

@dataclass(frozen=True)
class QAResult:
    generation: GenerationResult
    retrieved: list[RRFResult]

class HybridQAService:
    def __init__(self, bm25_index: Path = Path("data/indexes/bm25"), dense_index: Path = Path("data/indexes/faiss"), model: str = "BAAI/bge-small-en-v1.5", device: str = "cpu", cache_dir: Path = Path(".modal_cache"), retrieval_k: int = 50, rrf_k: int = 60, top_k: int = 8, generator: OllamaGenerator | None = None) -> None:
        if retrieval_k <= 0 or rrf_k <= 0 or top_k <= 0:
            raise ValueError("retrieval_k, rrf_k, and top_k must be greater than zero")
        self.bm25 = BM25Retriever(bm25_index)
        self.dense = DenseRetriever(dense_index, model, device, cache_dir)
        self.rrf_k = rrf_k
        self.retrieval_k = retrieval_k
        self.top_k = top_k
        self.generator = generator or OllamaGenerator()

    def answer(self, query: str) -> QAResult:
        if not query.strip():
            raise ValueError("query must not be empty")
        bm25_results = self.bm25.retrieve(query, self.retrieval_k)
        dense_results = self.dense.retrieve(query, self.retrieval_k)
        fused = reciprocal_rank_fusion(bm25_results, dense_results, self.rrf_k, self.top_k)
        generation = self.generator.generate(query, fused)
        return QAResult(generation=generation, retrieved=fused)
