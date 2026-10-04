from types import SimpleNamespace

from fastapi.testclient import TestClient

from retrieval.rrf import RRFResult
from backend.app import create_app
from generation.groq import GroqRateLimitError


class FakeService:
    def answer(self, query):
        return SimpleNamespace(
            generation=SimpleNamespace(
                answer="[SOURCE: c1] Bail.",
                model="openai/gpt-oss-120b",
                citations=["c1"],
            ),
            retrieved=[RRFResult("c1", "d1", "Bail.", 0.1, 1, 1, {})],
        )


def test_health():
    client = TestClient(create_app(FakeService()))
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_qa_endpoint():
    client = TestClient(create_app(FakeService()))
    response = client.post("/qa", json={"query": "What is bail?"})
    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "[SOURCE: c1] Bail."
    assert body["model"] == "openai/gpt-oss-120b"
    assert body["citations"] == ["c1"]
    assert body["retrieved_chunks"][0]["chunk_id"] == "c1"


def test_qa_rejects_empty_query():
    client = TestClient(create_app(FakeService()))
    response = client.post("/qa", json={"query": ""})
    assert response.status_code == 422


class TimeoutService:
    def answer(self, query):
        raise TimeoutError("Groq generation timed out.")


def test_qa_maps_generation_timeout():
    client = TestClient(create_app(TimeoutService()))
    response = client.post("/qa", json={"query": "What is bail?"})
    assert response.status_code == 504
    assert "timed out" in response.json()["detail"]


class RateLimitService:
    def answer(self, query):
        raise GroqRateLimitError("Groq rate limit remained exceeded after retries.")


def test_qa_maps_rate_limit_to_too_many_requests():
    client = TestClient(create_app(RateLimitService()))
    response = client.post("/qa", json={"query": "What is bail?"})
    assert response.status_code == 429
    assert "rate limit" in response.json()["detail"]


class SearchService:
    def retrieve(self, query, top_k=None):
        return [RRFResult("c1", "d1", "Bail provision", 0.1, 1, 2, {"doc_type": "judgment"})]


def test_search_endpoint():
    client = TestClient(create_app(SearchService()))
    response = client.post("/search", json={"query": "bail"})
    assert response.status_code == 200
    assert response.json()["results"][0]["chunk_id"] == "c1"


def test_search_rejects_empty_query():
    client = TestClient(create_app(SearchService()))
    response = client.post("/search", json={"query": ""})
    assert response.status_code == 422


class DocumentService:
    def __init__(self):
        self.generator = object()

    def answer_from_results(self, query, results):
        return SimpleNamespace(
            generation=SimpleNamespace(answer="[SOURCE: upload:0] Finding.", model="openai/gpt-oss-120b", citations=["upload:0"]),
            retrieved=results,
        )


def test_document_analysis_rejects_non_pdf():
    client = TestClient(create_app(DocumentService()))
    response = client.post("/document-analysis", files={"file": ("note.txt", b"text", "text/plain")}, data={"query": "What does it say?"})
    assert response.status_code == 400


def test_document_analysis_rejects_empty_pdf():
    client = TestClient(create_app(DocumentService()))
    response = client.post("/document-analysis", files={"file": ("note.pdf", b"", "application/pdf")}, data={"query": "What does it say?"})
    assert response.status_code == 400
