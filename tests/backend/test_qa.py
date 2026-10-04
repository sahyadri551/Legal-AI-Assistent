from pathlib import Path
from types import SimpleNamespace
from retrieval.bm25 import BM25Result
from retrieval.dense import DenseResult
from retrieval.rrf import RRFResult
from backend.qa import HybridQAService

class FakeBM25:
    def retrieve(self, query, top_k):
        return [BM25Result("c1", "d1", "Section 439 concerns bail.", 1.0, 1, {})]

class FakeDense:
    def retrieve(self, query, top_k):
        return [DenseResult("c1", "d1", "Section 439 concerns bail.", 0.9, 1, {})]

class FakeGenerator:
    def generate(self, query, results):
        assert query == "What is bail?"
        assert [r.chunk_id for r in results] == ["c1"]
        return SimpleNamespace(answer="[SOURCE: c1] Section 439 concerns bail.", model="qwen3:4b", citations=["c1"])

def test_answer_runs_bm25_dense_rrf_and_generation():
    service = object.__new__(HybridQAService)
    service.bm25 = FakeBM25()
    service.dense = FakeDense()
    service.retrieval_k = 50
    service.rrf_k = 60
    service.top_k = 8
    service.generator = FakeGenerator()
    result = service.answer("What is bail?")
    assert result.generation.answer.startswith("[SOURCE: c1]")
    assert result.retrieved[0].chunk_id == "c1"

def test_answer_rejects_empty_query():
    service = object.__new__(HybridQAService)
    service.bm25 = FakeBM25()
    service.dense = FakeDense()
    service.retrieval_k = 50
    service.rrf_k = 60
    service.top_k = 8
    service.generator = FakeGenerator()
    try:
        service.answer("   ")
    except ValueError as exc:
        assert "query must not be empty" in str(exc)
    else:
        raise AssertionError("expected ValueError")
