"""Grounded answer generation using a local Ollama model."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Protocol

from ollama import ResponseError

from retrieval.rrf import RRFResult


class ChatClient(Protocol):
    def chat(self, **kwargs: Any) -> Any: ...


@dataclass(frozen=True)
class GenerationResult:
    answer: str
    model: str
    citations: list[str]


class OllamaGenerator:
    RESPONSE_SCHEMA = {
        "type": "object",
        "properties": {
            "answer": {
                "type": "string",
                "description": "Only the final legal answer grounded in the retrieved excerpts.",
            }
        },
        "required": ["answer"],
    }

    def __init__(
        self,
        model: str = "qwen3:4b",
        base_url: str = "http://127.0.0.1:11434",
        timeout_seconds: int = 300,
        temperature: float = 0.2,
        top_p: float = 0.9,
        num_predict: int = 384,
        num_ctx: int = 2048,
        max_chunks: int = 8,
        max_context_chars: int = 4500,
        system_prompt: str = (
            "You are a research assistant for Indian legal questions. "
            "Answer only from the provided retrieved excerpts. "
            "Cite the source identifiers given with those excerpts. "
            "If the excerpts are insufficient, say so. "
            "Do not invent law, citations, or case holdings. "
            "Return the answer only through the required JSON object. "
            "The answer field must contain only the final answer, never "
            "reasoning, analysis, planning, or commentary about generating "
            "the answer."
        ),
        client: ChatClient | None = None,
    ) -> None:
        if not model.strip():
            raise ValueError("model must not be empty")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero")
        if num_predict <= 0 or num_ctx <= 0:
            raise ValueError("generation limits must be greater than zero")
        if max_chunks <= 0 or max_context_chars <= 0:
            raise ValueError("context limits must be greater than zero")

        if client is None:
            from ollama import Client

            client = Client(host=base_url, timeout=timeout_seconds)

        self.client = client
        self.model = model
        self.temperature = temperature
        self.top_p = top_p
        self.num_predict = num_predict
        self.num_ctx = num_ctx
        self.max_chunks = max_chunks
        self.max_context_chars = max_context_chars
        self.system_prompt = system_prompt

    def build_prompt(self, query: str, results: list[RRFResult]) -> str:
        if not query.strip():
            raise ValueError("query must not be empty")

        excerpts: list[str] = []
        used = 0

        for result in results[: self.max_chunks]:
            block = f"[SOURCE: {result.chunk_id}]\n{result.text.strip()}"
            if used + len(block) > self.max_context_chars:
                remaining = self.max_context_chars - used
                if remaining <= 0:
                    break
                block = block[:remaining]

            excerpts.append(block)
            used += len(block)

            if used >= self.max_context_chars:
                break

        context = "\n\n".join(excerpts) if excerpts else "[NO RETRIEVED EXCERPTS]"

        return (
            f"Question:\n{query.strip()}\n\n"
            f"Retrieved excerpts:\n{context}\n\n"
            "Return a JSON object with exactly one field named "
            '"answer". The answer field must contain only the final answer '
            "to the question. Do not put analysis, reasoning, planning, "
            "or commentary in it. Use only the retrieved excerpts. "
            "Cite each material claim with its [SOURCE: ...] identifier. "
            "If the excerpts do not support an answer, state that the "
            "retrieved excerpts are insufficient."
        )

    @staticmethod
    def _streamed_content(response: Any) -> str:
        parts: list[str] = []

        for chunk in response:
            message = getattr(chunk, "message", None)
            content = getattr(message, "content", None) if message is not None else None

            if content is None and isinstance(chunk, dict):
                content = chunk.get("message", {}).get("content")

            if content:
                parts.append(str(content))

        return "".join(parts)

    @staticmethod
    def _extract_answer(content: str) -> str:
        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Ollama returned malformed structured output") from exc

        if not isinstance(payload, dict):
            raise RuntimeError("Ollama structured output must be a JSON object")

        answer = payload.get("answer")
        if not isinstance(answer, str) or not answer.strip():
            raise RuntimeError("Ollama structured output contains no answer")

        return answer.strip()

    def generate(self, query: str, results: list[RRFResult]) -> GenerationResult:
        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": self.build_prompt(query, results)},
                ],
                stream=True,
                think=False,
                keep_alive="10m",
                format=self.RESPONSE_SCHEMA,
                options={
                    "temperature": self.temperature,
                    "top_p": self.top_p,
                    "num_ctx": self.num_ctx,
                    "num_predict": self.num_predict,
                },
            )
            content = self._streamed_content(response)
        except ResponseError as exc:
            message = str(exc)
            lowered = message.lower()
            if "out-of-memory" in lowered or "failed to allocate" in lowered:
                raise RuntimeError(
                    "Ollama ran out of CPU memory while starting the model context. "
                    "The application requests a 2048-token context; close other "
                    "memory-heavy applications or use a smaller Ollama model if "
                    "the machine still cannot allocate the model."
                ) from exc
            raise RuntimeError(f"Ollama request failed: {message}") from exc

        if not content and hasattr(response, "message"):
            content = getattr(response.message, "content", None) or ""

        if not content and isinstance(response, dict):
            content = response.get("message", {}).get("content", "")

        if not content or not str(content).strip():
            raise RuntimeError("Ollama returned an empty answer")

        answer = self._extract_answer(str(content).strip())
        citations = [
            result.chunk_id
            for result in results[: self.max_chunks]
            if result.chunk_id in answer
        ]

        return GenerationResult(answer, self.model, citations)
