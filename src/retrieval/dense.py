"""Dense embedding and FAISS retrieval."""
from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol
import faiss
import numpy as np

class Encoder(Protocol):
    def encode(self, sentences: list[str], **kwargs: Any) -> np.ndarray: ...

@dataclass(frozen=True)
class DenseResult:
    chunk_id: str
    doc_id: str
    text: str
    score: float
    rank: int
    metadata: dict[str, Any]

class SentenceTransformerEncoder:
    def __init__(self, model_name: str, device: str = "cpu") -> None:
        if device != "cpu":
            raise ValueError("Milestone 5 is CPU-only; device must be 'cpu'")
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name, device="cpu")

    def encode(self, sentences: list[str], **kwargs: Any) -> np.ndarray:
        embeddings = self.model.encode(sentences, convert_to_numpy=True, normalize_embeddings=True,
                                       show_progress_bar=False, **kwargs)
        return np.asarray(embeddings, dtype=np.float32)

class DenseIndex:
    FORMAT_VERSION = 1
    def __init__(self, index: faiss.Index, records: list[dict[str, Any]]) -> None:
        if index.ntotal != len(records):
            raise ValueError("FAISS index and records must have equal length")
        self.index, self.records = index, records

    @classmethod
    def build(cls, records: list[dict[str, Any]], embeddings: np.ndarray) -> "DenseIndex":
        if not records:
            raise ValueError("cannot build dense index from empty corpus")
        vectors = _prepare_embeddings(embeddings, len(records))
        index = faiss.IndexFlatIP(vectors.shape[1])
        index.add(vectors)
        return cls(index, records)

    def save(self, output_dir: Path) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(output_dir / "index.faiss"))
        (output_dir / "records.jsonl").write_text(
            "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in self.records),
            encoding="utf-8")
        (output_dir / "manifest.json").write_text(json.dumps({
            "format_version": self.FORMAT_VERSION, "index_type": "IndexFlatIP",
            "dimension": self.index.d, "chunks": len(self.records),
            "documents": len({r["doc_id"] for r in self.records}),
            "index_file": "index.faiss", "records_file": "records.jsonl"}, indent=2),
            encoding="utf-8")

    @classmethod
    def load(cls, index_dir: Path) -> "DenseIndex":
        manifest = json.loads((index_dir / "manifest.json").read_text(encoding="utf-8"))
        if manifest.get("format_version") != cls.FORMAT_VERSION:
            raise ValueError("unsupported dense index format")
        index = faiss.read_index(str(index_dir / "index.faiss"))
        records = [json.loads(line) for line in
                   (index_dir / "records.jsonl").read_text(encoding="utf-8").splitlines()
                   if line.strip()]
        return cls(index, records)

    def search(self, query_embedding: np.ndarray, top_k: int = 8) -> list[DenseResult]:
        if top_k <= 0:
            raise ValueError("top_k must be greater than zero")
        query = _prepare_embeddings(query_embedding, 1)
        limit = min(top_k, len(self.records))
        scores, indices = self.index.search(query, limit)
        results = []
        for rank, (score, idx) in enumerate(zip(scores[0], indices[0]), 1):
            if idx < 0:
                continue
            record = self.records[int(idx)]
            metadata = {k: v for k, v in record.items() if k not in {"chunk_id", "doc_id", "text"}}
            results.append(DenseResult(str(record["chunk_id"]), str(record["doc_id"]),
                str(record.get("text") or ""), float(score), rank, metadata))
        return results

def _prepare_embeddings(embeddings: np.ndarray, expected_rows: int) -> np.ndarray:
    vectors = np.asarray(embeddings, dtype=np.float32)
    if vectors.ndim == 1:
        vectors = vectors.reshape(1, -1)
    if vectors.ndim != 2 or vectors.shape[0] != expected_rows:
        raise ValueError("embeddings must be a 2D array with the expected number of rows")
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    if np.any(norms == 0):
        raise ValueError("embeddings must not contain zero vectors")
    return vectors / norms

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

def build_dense_index(chunks_path: Path, output_dir: Path, model_name: str = "BAAI/bge-small-en-v1.5",
                      device: str = "cpu", batch_size: int = 8) -> dict[str, int | str]:
    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero")
    records = _load_chunk_records(chunks_path)
    if not records:
        raise ValueError("cannot build dense index from empty corpus")
    encoder = SentenceTransformerEncoder(model_name, device=device)
    embeddings = encoder.encode([str(r.get("text") or "") for r in records], batch_size=batch_size)
    index = DenseIndex.build(records, embeddings)
    index.save(output_dir)
    return {"chunks": len(records), "documents": len({r["doc_id"] for r in records}),
            "dimension": index.index.d, "model": model_name, "device": device,
            "output_dir": str(output_dir)}

class DenseRetriever:
    def __init__(self, index_dir: Path, model_name: str = "BAAI/bge-small-en-v1.5",
                 device: str = "cpu") -> None:
        self.encoder = SentenceTransformerEncoder(model_name, device=device)
        self.index = DenseIndex.load(index_dir)
    def retrieve(self, query: str, top_k: int = 8) -> list[DenseResult]:
        if not query.strip():
            return []
        return self.index.search(self.encoder.encode([query]), top_k=top_k)
