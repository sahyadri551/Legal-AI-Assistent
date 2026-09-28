"""Deterministic character-bounded chunking for normalized legal documents."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _chunk_text(text: str, max_chars: int, overlap_chars: int) -> list[str]:
    if max_chars <= 0:
        raise ValueError("max_chars must be greater than zero")
    if overlap_chars < 0 or overlap_chars >= max_chars:
        raise ValueError("overlap_chars must be >= 0 and < max_chars")

    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(words):
        current: list[str] = []
        length = 0
        end = start
        while end < len(words):
            word = words[end]
            added = len(word) if not current else len(word) + 1
            if current and length + added > max_chars:
                break
            current.append(word)
            length += added
            end += 1

        chunk = " ".join(current).strip()
        if chunk:
            chunks.append(chunk)

        if end >= len(words):
            break

        if overlap_chars == 0:
            start = end
            continue

        overlap_len = 0
        overlap_start = end
        while overlap_start > start:
            word_len = len(words[overlap_start - 1])
            added = word_len if overlap_len == 0 else word_len + 1
            if overlap_len + added > overlap_chars:
                break
            overlap_len += added
            overlap_start -= 1
        start = max(start + 1, overlap_start)

    return chunks


def chunk_documents(
    input_path: Path,
    output_path: Path,
    max_chars: int = 1200,
    overlap_chars: int = 150,
) -> dict[str, int | float]:
    """Read documents.jsonl and write deterministic chunks.jsonl."""
    total_documents = 0
    total_chunks = 0
    zero_text_documents = 0
    chunk_lengths: list[int] = []

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with input_path.open("r", encoding="utf-8") as source, output_path.open(
        "w", encoding="utf-8", newline="\n"
    ) as target:
        for line in source:
            if not line.strip():
                continue
            document: dict[str, Any] = json.loads(line)
            total_documents += 1
            text = str(document.get("text") or "")
            chunks = _chunk_text(text, max_chars, overlap_chars)
            if not chunks:
                zero_text_documents += 1

            for index, chunk in enumerate(chunks):
                record = {
                    "chunk_id": f"{document['doc_id']}:{index}",
                    "doc_id": document["doc_id"],
                    "doc_type": document["doc_type"],
                    "pair_id": document.get("pair_id"),
                    "source_pdf": document["source_pdf"],
                    "caption_path": document.get("caption_path"),
                    "caption_text": document.get("caption_text"),
                    "pdf_filename": document["pdf_filename"],
                    "chunk_index": index,
                    "text": chunk,
                    "char_count": len(chunk),
                }
                target.write(json.dumps(record, ensure_ascii=False) + "\n")
                total_chunks += 1
                chunk_lengths.append(len(chunk))

    return {
        "documents": total_documents,
        "chunks": total_chunks,
        "zero_text_documents": zero_text_documents,
        "min_chunk_chars": min(chunk_lengths) if chunk_lengths else 0,
        "max_chunk_chars": max(chunk_lengths) if chunk_lengths else 0,
        "avg_chunk_chars": (
            sum(chunk_lengths) / len(chunk_lengths) if chunk_lengths else 0.0
        ),
    }
