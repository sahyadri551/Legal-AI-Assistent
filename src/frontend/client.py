"""HTTP client for the FastAPI legal QA backend."""
from __future__ import annotations

from dataclasses import dataclass
import base64
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

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            response = httpx.post(
                f"{self.base_url}{path}",
                json=payload,
                timeout=self.timeout,
            )
        except httpx.TimeoutException as exc:
            raise BackendError("The backend timed out while processing the request.") from exc
        except httpx.HTTPError as exc:
            raise BackendError(f"Could not reach the backend: {exc}") from exc

        if response.is_error:
            try:
                detail = response.json().get("detail", response.text)
            except ValueError:
                detail = response.text
            raise BackendError(f"Backend returned HTTP {response.status_code}: {detail}")
        return response.json()

    def ask(self, query: str) -> QAAnswer:
        if not query.strip():
            raise ValueError("Please enter a legal question.")
        body = self._post("/qa", {"query": query.strip()})
        return QAAnswer(
            answer=body["answer"],
            model=body["model"],
            citations=body.get("citations", []),
            retrieved_chunks=body.get("retrieved_chunks", []),
        )

    def analyze_document(
        self,
        filename: str,
        content: bytes,
        instruction: str,
    ) -> dict[str, Any]:
        if not content:
            raise ValueError("The uploaded document is empty.")
        if not filename.lower().endswith(".pdf"):
            raise ValueError("Document analysis currently supports PDF files only.")
        if not instruction.strip():
            raise ValueError("Please provide an analysis instruction.")
        return self._post(
            "/document-analysis",
            {
                "filename": filename,
                "content_base64": base64.b64encode(content).decode("ascii"),
                "instruction": instruction.strip(),
            },
        )

    def search_case_law(self, query: str, top_k: int = 8) -> list[dict[str, Any]]:
        if not query.strip():
            raise ValueError("Please enter a case-law search query.")
        if top_k <= 0:
            raise ValueError("top_k must be greater than zero.")
        body = self._post(
            "/case-law/search",
            {"query": query.strip(), "top_k": int(top_k)},
        )
        return list(body.get("results", []))
