"""HTTP client for the FastAPI legal QA backend."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


class BackendError(RuntimeError):
    """Raised when the backend cannot complete a request."""


@dataclass(frozen=True)
class QAAnswer:
    answer: str
    model: str
    citations: list[str]
    retrieved_chunks: list[dict[str, Any]]


class LegalQAClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000", timeout: float = 180.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def health(self) -> bool:
        try:
            response = httpx.get(f"{self.base_url}/health", timeout=10.0)
            response.raise_for_status()
            return response.json().get("status") == "ok"
        except httpx.HTTPError as exc:
            raise BackendError(f"Backend health check failed: {exc}") from exc

    def ask(self, query: str) -> QAAnswer:
        if not query.strip():
            raise ValueError("Please enter a legal question.")
        try:
            response = httpx.post(
                f"{self.base_url}/qa",
                json={"query": query.strip()},
                timeout=self.timeout,
            )
        except httpx.TimeoutException as exc:
            raise BackendError("The backend timed out while generating the answer.") from exc
        except httpx.HTTPError as exc:
            raise BackendError(f"Could not reach the backend: {exc}") from exc

        if response.is_error:
            try:
                detail = response.json().get("detail", response.text)
            except ValueError:
                detail = response.text
            raise BackendError(f"Backend returned HTTP {response.status_code}: {detail}")

        body = response.json()
        return QAAnswer(
            answer=body["answer"],
            model=body["model"],
            citations=body.get("citations", []),
            retrieved_chunks=body.get("retrieved_chunks", []),
        )
