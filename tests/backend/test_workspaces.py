from types import SimpleNamespace

from fastapi.testclient import TestClient

from backend.app import create_app


class FakeWorkspace:
    def search_case_law(self, query, top_k):
        return [{"chunk_id": "judgment:1:0", "doc_id": "judgment:1", "text": "Bail.", "score": 0.1}]

    def analyze_document(self, filename, content, instruction):
        assert filename == "notice.pdf"
        assert content == b"%PDF-"
        return {
            "filename": filename,
            "pages": 1,
            "model": "openai/gpt-oss-120b",
            "answer": "[SOURCE: 1] Grounded.",
            "citations": ["1"],
            "sources": [{"chunk_id": "page:1", "text": "Notice", "metadata": {"page": 1}}],
        }


def test_case_law_search_endpoint():
    app = create_app(SimpleNamespace(answer=lambda query: None))
    app.state.workspace = FakeWorkspace()
    client = TestClient(app)
    response = client.post("/case-law/search", json={"query": "bail", "top_k": 8})
    assert response.status_code == 200
    assert response.json()["results"][0]["doc_id"] == "judgment:1"


def test_document_analysis_endpoint():
    app = create_app(SimpleNamespace(answer=lambda query: None))
    app.state.workspace = FakeWorkspace()
    client = TestClient(app)
    import base64
    response = client.post(
        "/document-analysis",
        json={
            "filename": "notice.pdf",
            "content_base64": base64.b64encode(b"%PDF-").decode("ascii"),
            "instruction": "Summarize.",
        },
    )
    assert response.status_code == 200
    assert response.json()["pages"] == 1
    assert response.json()["citations"] == ["1"]
