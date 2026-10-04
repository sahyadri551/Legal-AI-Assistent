from types import SimpleNamespace
import httpx
from fastapi.testclient import TestClient
from retrieval.rrf import RRFResult
from backend.app import create_app

class FakeService:
    def answer(self, query):
        return SimpleNamespace(
            generation=SimpleNamespace(answer="[SOURCE: c1] Bail.", model="qwen3:4b", citations=["c1"]),
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
    assert body["citations"] == ["c1"]
    assert body["retrieved_chunks"][0]["chunk_id"] == "c1"

def test_qa_rejects_empty_query():
    client = TestClient(create_app(FakeService()))
    response = client.post("/qa", json={"query": ""})
    assert response.status_code == 422

class TimeoutService:
    def answer(self, query):
        raise httpx.ReadTimeout("generation timed out")

def test_qa_maps_generation_timeout():
    client = TestClient(create_app(TimeoutService()))
    response = client.post("/qa", json={"query": "What is bail?"})
    assert response.status_code == 504
    assert "timed out" in response.json()["detail"]


class OOMService:
    def answer(self, query):
        raise RuntimeError(
            "Ollama ran out of CPU memory while starting the model context."
        )


def test_qa_maps_ollama_oom_to_service_unavailable():
    client = TestClient(create_app(OOMService()))
    response = client.post("/qa", json={"query": "What is bail?"})
    assert response.status_code == 503
    assert "ran out of CPU memory" in response.json()["detail"]
