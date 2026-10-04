from __future__ import annotations

import httpx
import pytest

from frontend.client import BackendError, LegalQAClient


def test_health_uses_backend(monkeypatch):
    def fake_get(url, timeout):
        assert url.endswith("/health")
        return httpx.Response(200, json={"status": "ok"})

    monkeypatch.setattr(httpx, "get", fake_get)
    assert LegalQAClient().health() is True


def test_ask_parses_response(monkeypatch):
    def fake_post(url, json, timeout):
        assert json == {"query": "What is bail?"}
        return httpx.Response(
            200,
            json={
                "answer": "[SOURCE: c1] Bail.",
                "model": "qwen3:4b",
                "citations": ["c1"],
                "retrieved_chunks": [{"chunk_id": "c1", "text": "Bail."}],
            },
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
        return httpx.Response(503, json={"detail": "Indexes unavailable"})

    monkeypatch.setattr(httpx, "post", fake_post)
    with pytest.raises(BackendError, match="Indexes unavailable"):
        LegalQAClient().ask("What is bail?")
