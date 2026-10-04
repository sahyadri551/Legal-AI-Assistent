"""Grounded answer generation using a local Ollama model."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Protocol
from retrieval.rrf import RRFResult

class ChatClient(Protocol):
    def chat(self, **kwargs: Any) -> Any: ...

@dataclass(frozen=True)
class GenerationResult:
    answer: str
    model: str
    citations: list[str]

class OllamaGenerator:
    def __init__(self, model="qwen3:4b", base_url="http://127.0.0.1:11434", timeout_seconds=120, temperature=0.2, top_p=0.9, num_predict=512, max_chunks=8, max_context_chars=6000, system_prompt=("You are a research assistant for Indian legal questions. Answer only from the provided retrieved excerpts. Cite the source identifiers given with those excerpts. If the excerpts are insufficient, say so. Do not invent law, citations, or case holdings."), client=None):
        if not model.strip(): raise ValueError("model must not be empty")
        if max_chunks <= 0 or max_context_chars <= 0: raise ValueError("context limits must be greater than zero")
        if client is None:
            from ollama import Client
            client = Client(host=base_url, timeout=timeout_seconds)
        self.client=client; self.model=model; self.temperature=temperature; self.top_p=top_p; self.num_predict=num_predict; self.max_chunks=max_chunks; self.max_context_chars=max_context_chars; self.system_prompt=system_prompt

    def build_prompt(self, query: str, results: list[RRFResult]) -> str:
        if not query.strip(): raise ValueError("query must not be empty")
        excerpts=[]; used=0
        for result in results[:self.max_chunks]:
            block=f"[SOURCE: {result.chunk_id}]\n{result.text.strip()}"
            if used + len(block) > self.max_context_chars:
                remaining=self.max_context_chars-used
                if remaining <= 0: break
                block=block[:remaining]
            excerpts.append(block); used += len(block)
            if used >= self.max_context_chars: break
        context="\n\n".join(excerpts) if excerpts else "[NO RETRIEVED EXCERPTS]"
        return f"Question:\n{query.strip()}\n\nRetrieved excerpts:\n{context}\n\nAnswer using only these excerpts. Cite each material claim with its [SOURCE: ...] identifier. If the excerpts do not support an answer, state that the retrieved excerpts are insufficient."

    def generate(self, query: str, results: list[RRFResult]) -> GenerationResult:
        response=self.client.chat(model=self.model, messages=[{"role":"system","content":self.system_prompt},{"role":"user","content":self.build_prompt(query, results)}], options={"temperature":self.temperature,"top_p":self.top_p,"num_predict":self.num_predict})
        message=getattr(response,"message",None); answer=getattr(message,"content",None) if message is not None else None
        if not answer and isinstance(response,dict): answer=response.get("message",{}).get("content")
        if not answer or not str(answer).strip(): raise RuntimeError("Ollama returned an empty answer")
        answer=str(answer).strip()
        citations=[r.chunk_id for r in results[:self.max_chunks] if r.chunk_id in answer]
        return GenerationResult(answer,self.model,citations)
