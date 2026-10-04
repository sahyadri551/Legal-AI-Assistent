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


def test_client_uses_backend_url_env(monkeypatch):
    monkeypatch.setenv("BACKEND_URL", "https://legal-ai-backend.example.com")
    client = LegalQAClient()
    assert client.base_url == "https://legal-ai-backend.example.com"


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


class FakeHTTPResponse:
    def __init__(self, body, status=200):
        self._body = body
        self.status_code = status
        self.text = str(body)
        self.is_error = status >= 400

    def json(self):
        return self._body

    def raise_for_status(self):
        if self.is_error:
            raise RuntimeError("error")


def test_search(monkeypatch):
    monkeypatch.setattr("httpx.post", lambda *a, **k: FakeHTTPResponse({"results": [{"chunk_id": "c1"}]}))
    assert LegalQAClient().search("bail")[0]["chunk_id"] == "c1"


def test_analyze_document(monkeypatch):
    body = {"answer": "Finding", "model": "openai/gpt-oss-120b", "citations": [], "retrieved_chunks": []}
    monkeypatch.setattr("httpx.post", lambda *a, **k: FakeHTTPResponse(body))
    result = LegalQAClient().analyze_document(b"pdf", "case.pdf", "summarize")
    assert result.answer == "Finding"
