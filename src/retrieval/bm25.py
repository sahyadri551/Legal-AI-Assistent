"""BM25 index persistence and retrieval over chunk JSONL records."""

from __future__ import annotations

import json
import pickle
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rank_bm25 import BM25Okapi

_TOKEN_RE = re.compile(r"[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)*")


def tokenize(text: str) -> list[str]:
    return [match.group(0).lower() for match in _TOKEN_RE.finditer(text)]


@dataclass(frozen=True)
class BM25Result:
    chunk_id: str
    doc_id: str
    text: str
    score: float
    rank: int
    metadata: dict[str, Any]


class BM25Index:
    FORMAT_VERSION = 1

    def __init__(self, bm25: BM25Okapi, records: list[dict[str, Any]], corpus_tokens: list[list[str]]) -> None:
        if len(records) != len(corpus_tokens):
            raise ValueError("records and corpus_tokens must have equal length")
        self.bm25 = bm25
        self.records = records
        self.corpus_tokens = corpus_tokens

    @classmethod
    def build(cls, records: list[dict[str, Any]]) -> "BM25Index":
        if not records:
            raise ValueError("cannot build BM25 index from empty corpus")
        tokens = [tokenize(str(record.get("text") or "")) for record in records]
        return cls(BM25Okapi(tokens), records, tokens)

    def save(self, output_dir: Path) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        with (output_dir / "index.pkl").open("wb") as handle:
            pickle.dump(
                {"format_version": self.FORMAT_VERSION, "records": self.records,
                 "corpus_tokens": self.corpus_tokens, "bm25": self.bm25},
                handle, protocol=pickle.HIGHEST_PROTOCOL,
            )
        (output_dir / "manifest.json").write_text(
            json.dumps({
                "format_version": self.FORMAT_VERSION,
                "documents": len({r["doc_id"] for r in self.records}),
                "chunks": len(self.records),
                "index_file": "index.pkl",
            }, indent=2), encoding="utf-8"
        )

    @classmethod
    def load(cls, index_dir: Path) -> "BM25Index":
        with (index_dir / "index.pkl").open("rb") as handle:
            payload = pickle.load(handle)
        if payload.get("format_version") != cls.FORMAT_VERSION:
            raise ValueError("unsupported BM25 index format")
        return cls(payload["bm25"], payload["records"], payload["corpus_tokens"])

    def search(self, query: str, top_k: int = 8) -> list[BM25Result]:
        if top_k <= 0:
            raise ValueError("top_k must be greater than zero")
        query_tokens = tokenize(query)
        if not query_tokens:
            return []
        scores = self.bm25.get_scores(query_tokens)
        ranked = sorted(range(len(scores)), key=lambda i: (-float(scores[i]), i))[:top_k]
        results = []
        for rank, index in enumerate(ranked, 1):
            record = self.records[index]
            metadata = {k: v for k, v in record.items() if k not in {"chunk_id", "doc_id", "text"}}
            results.append(BM25Result(
                chunk_id=str(record["chunk_id"]), doc_id=str(record["doc_id"]),
                text=str(record.get("text") or ""), score=float(scores[index]),
                rank=rank, metadata=metadata,
            ))
        return results


def _load_chunk_records(chunks_path: Path) -> list[dict[str, Any]]:
    records = []
    with chunks_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON on line {line_number}") from exc
            for field in ("chunk_id", "doc_id", "text"):
                if field not in record:
                    raise ValueError(f"missing required field {field!r} on line {line_number}")
            records.append(record)
    return records


def build_bm25_index(chunks_path: Path, output_dir: Path) -> dict[str, int | str]:
    records = _load_chunk_records(chunks_path)
    index = BM25Index.build(records)
    index.save(output_dir)
    return {"chunks": len(records), "documents": len({r["doc_id"] for r in records}), "output_dir": str(output_dir)}


class BM25Retriever:
    def __init__(self, index_dir: Path) -> None:
        self.index = BM25Index.load(index_dir)

    def retrieve(self, query: str, top_k: int = 8) -> list[BM25Result]:
        return self.index.search(query, top_k)
