from __future__ import annotations

import httpx
import pytest

from frontend.client import BackendError, LegalQAClient


def test_health_uses_backend(monkeypatch):
    def fake_get(url, timeout):
        assert url.endswith("/health")
        return httpx.Response(
            200,
            json={"status": "ok"},
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx, "get", fake_get)
    assert LegalQAClient().health() is True


def test_ask_parses_response(monkeypatch):
    def fake_post(url, json, timeout):
        assert json == {"query": "What is bail?"}
        return httpx.Response(
            200,
            json={
                "answer": "[SOURCE: c1] Bail.",
                "model": "openai/gpt-oss-120b",
                "citations": ["c1"],
                "retrieved_chunks": [{"chunk_id": "c1", "text": "Bail."}],
            },
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx, "post", fake_post)
    result = LegalQAClient().ask("What is bail?")
    assert result.answer == "[SOURCE: c1] Bail."
    assert result.citations == ["c1"]


def test_ask_rejects_empty_query():
    with pytest.raises(ValueError, match="legal question"):
        LegalQAClient().ask("   ")


def test_ask_reports_backend_error(monkeypatch):
    def fake_post(url, json, timeout):
        return httpx.Response(
            503,
            json={"detail": "Indexes unavailable"},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx, "post", fake_post)
    with pytest.raises(BackendError, match="Indexes unavailable"):
        LegalQAClient().ask("What is bail?")


def test_case_law_search_posts_query(monkeypatch):
    def fake_post(url, json, timeout):
        assert url.endswith("/case-law/search")
        assert json == {"query": "bail", "top_k": 5}
        return httpx.Response(200, json={"results": [{"chunk_id": "judgment:1:0"}]}, request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx, "post", fake_post)
    assert LegalQAClient().search_case_law("bail", 5)[0]["chunk_id"] == "judgment:1:0"


def test_document_analysis_posts_base64(monkeypatch):
    def fake_post(url, json, timeout):
        assert url.endswith("/document-analysis")
        assert json["filename"] == "x.pdf"
        assert json["content_base64"] == "aGVsbG8="
        return httpx.Response(200, json={"filename": "x.pdf", "pages": 1, "answer": "ok"}, request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx, "post", fake_post)
    assert LegalQAClient().analyze_document("x.pdf", b"hello", "Summarize")["answer"] == "ok"
