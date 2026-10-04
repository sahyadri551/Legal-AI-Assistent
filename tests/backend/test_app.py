from types import SimpleNamespace
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
