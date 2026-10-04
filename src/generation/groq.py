"""Grounded legal answer generation using Groq's OpenAI-compatible API."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Protocol

from dotenv import load_dotenv
from openai import APIError, APITimeoutError, OpenAI, RateLimitError

from retrieval.rrf import RRFResult


class ChatCompletionsClient(Protocol):
    @property
    def chat(self) -> Any: ...


class GroqRateLimitError(RuntimeError):
    """Groq rate limit remained exceeded after configured retries."""


@dataclass(frozen=True)
class GenerationResult:
    answer: str
    model: str
    citations: list[str]


class GroqGenerator:
    RESPONSE_SCHEMA = {
        "type": "json_schema",
        "json_schema": {
            "name": "legal_answer",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "answer": {
                        "type": "string",
                        "description": "Only the final legal answer grounded in the retrieved excerpts.",
                    }
                },
                "required": ["answer"],
                "additionalProperties": False,
            },
        },
    }

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout_seconds: int = 300,
        max_completion_tokens: int = 2048,
        temperature: float = 0.2,
        top_p: float = 0.9,
        reasoning_effort: str = "medium",
        max_chunks: int = 8,
        max_context_chars: int = 12000,
        max_retries: int = 5,
        retry_base_seconds: float = 1.0,
        system_prompt: str = (
            "You are a research assistant for Indian legal questions. "
            "Answer only from the provided retrieved excerpts. "
            "Cite the source identifiers given with those excerpts. "
            "If the excerpts are insufficient, say so. "
            "Do not invent law, citations, or case holdings. "
            "Return only the required JSON object. "
            "The answer field must contain only the final answer, never "
            "reasoning, analysis, planning, or commentary about generating "
            "the answer."
        ),
        client: ChatCompletionsClient | None = None,
        sleep_fn: Any = time.sleep,
    ) -> None:
        load_dotenv()

        resolved_model = model or os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
        resolved_base_url = base_url or os.getenv(
            "GROQ_BASE_URL", "https://api.groq.com/openai/v1"
        )

        if not resolved_model.strip():
            raise ValueError("model must not be empty")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero")
        if max_completion_tokens <= 0:
            raise ValueError("max_completion_tokens must be greater than zero")
        if max_chunks <= 0 or max_context_chars <= 0:
            raise ValueError("context limits must be greater than zero")
        if max_retries < 0:
            raise ValueError("max_retries must not be negative")
        if retry_base_seconds < 0:
            raise ValueError("retry_base_seconds must not be negative")
        if reasoning_effort not in {"low", "medium", "high"}:
            raise ValueError("reasoning_effort must be low, medium, or high")

        if client is None:
            resolved_key = api_key or os.getenv("GROQ_API_KEY")
            if not resolved_key:
                raise ValueError("GROQ_API_KEY is not set")
            client = OpenAI(
                api_key=resolved_key,
                base_url=resolved_base_url,
                timeout=timeout_seconds,
                max_retries=0,
            )

        self.client = client
        self.model = resolved_model
        self.timeout_seconds = timeout_seconds
        self.max_completion_tokens = max_completion_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.reasoning_effort = reasoning_effort
        self.max_chunks = max_chunks
        self.max_context_chars = max_context_chars
        self.max_retries = max_retries
        self.retry_base_seconds = retry_base_seconds
        self.system_prompt = system_prompt
        self.sleep_fn = sleep_fn

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
    def _extract_answer(content: str) -> str:
        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Groq returned malformed structured output") from exc

        if not isinstance(payload, dict):
            raise RuntimeError("Groq structured output must be a JSON object")

        answer = payload.get("answer")
        if not isinstance(answer, str) or not answer.strip():
            raise RuntimeError("Groq structured output contains no answer")

        return answer.strip()

    def _retry_delay(self, exc: RateLimitError, attempt: int) -> float:
        response = getattr(exc, "response", None)
        headers = getattr(response, "headers", {}) if response is not None else {}
        retry_after = headers.get("retry-after") if headers else None

        if retry_after is not None:
            try:
                return max(0.0, float(retry_after))
            except (TypeError, ValueError):
                pass

        return self.retry_base_seconds * (2 ** attempt)

    def generate_with_context(
        self,
        query: str,
        context_blocks: list[str],
        *,
        source_prefix: str = "SOURCE",
    ) -> GenerationResult:
        if not query.strip():
            raise ValueError("query must not be empty")
        if not context_blocks:
            raise ValueError("context must not be empty")

        excerpts: list[str] = []
        used = 0
        for index, block in enumerate(context_blocks[: self.max_chunks], 1):
            text = str(block).strip()
            if not text:
                continue
            item = f"[{source_prefix}: {index}]\n{text}"
            if used + len(item) > self.max_context_chars:
                remaining = self.max_context_chars - used
                if remaining <= 0:
                    break
                item = item[:remaining]
            excerpts.append(item)
            used += len(item)
            if used >= self.max_context_chars:
                break

        if not excerpts:
            raise ValueError("context must not be empty")

        context = "\n\n".join(excerpts)
        prompt = (
            f"Question:\n{query.strip()}\n\n"
            f"Retrieved excerpts:\n{context}\n\n"
            "Return a JSON object with exactly one field named "
            '"answer". The answer field must contain only the final answer. '
            "Use only the provided excerpts. Cite every material claim with "
            f"its [{source_prefix}: N] identifier. If the excerpts are insufficient, say so."
        )
        generated = self._generate_prompt(prompt)
        return generated

    def generate(self, query: str, results: list[RRFResult]) -> GenerationResult:
        prompt = self.build_prompt(query, results)
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt},
        ]

        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    top_p=self.top_p,
                    max_completion_tokens=self.max_completion_tokens,
                    reasoning_effort=self.reasoning_effort,
                    response_format=self.RESPONSE_SCHEMA,
                    stream=False,
                    extra_body={"include_reasoning": False},
                )
                content = response.choices[0].message.content or ""
                break
            except RateLimitError as exc:
                if attempt >= self.max_retries:
                    raise GroqRateLimitError(
                        "Groq rate limit remained exceeded after retries."
                    ) from exc
                self.sleep_fn(self._retry_delay(exc, attempt))
            except APITimeoutError as exc:
                raise TimeoutError("Groq generation timed out.") from exc
            except APIError as exc:
                raise RuntimeError(f"Groq request failed: {exc}") from exc
        else:
            raise RuntimeError("Groq generation failed without a response")

        if not str(content).strip():
            raise RuntimeError("Groq returned an empty answer")

        answer = self._extract_answer(str(content).strip())
        citations = [
            result.chunk_id
            for result in results[: self.max_chunks]
            if result.chunk_id in answer
        ]

        return GenerationResult(answer, self.model, citations)