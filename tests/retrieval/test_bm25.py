import json
from pathlib import Path

import pytest

from retrieval.bm25 import BM25Index, BM25Retriever, build_bm25_index, tokenize


def _write_chunks(path: Path) -> None:
    rows = [
        {"chunk_id": "judgment:1:0", "doc_id": "judgment:1", "doc_type": "judgment",
         "text": "The Supreme Court considered bail under section 439.", "source_pdf": "1.pdf"},
        {"chunk_id": "judgment:2:0", "doc_id": "judgment:2", "doc_type": "judgment",
         "text": "The court discussed contract damages and compensation.", "source_pdf": "2.pdf"},
        {"chunk_id": "statute:BNS:0", "doc_id": "statute:BNS", "doc_type": "statute",
         "text": "Section 103 concerns punishment for murder.", "source_pdf": "BNS.pdf"},
    ]
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_tokenize_lowercases_and_keeps_section_tokens() -> None:
    assert tokenize("Section 439 Cr.P.C.") == ["section", "439", "cr", "p", "c"]


def test_build_save_load_and_retrieve(tmp_path: Path) -> None:
    chunks = tmp_path / "chunks.jsonl"
    index_dir = tmp_path / "bm25"
    _write_chunks(chunks)
    report = build_bm25_index(chunks, index_dir)

    assert report["chunks"] == 3
    assert (index_dir / "index.pkl").exists()
    assert (index_dir / "manifest.json").exists()

    results = BM25Retriever(index_dir).retrieve("Supreme Court bail section 439", top_k=2)
    assert len(results) == 1
    assert results[0].chunk_id == "judgment:1:0"
    assert results[0].rank == 1
    assert results[0].score > results[1].score


def test_empty_query_returns_no_results(tmp_path: Path) -> None:
    chunks = tmp_path / "chunks.jsonl"
    _write_chunks(chunks)
    records = [json.loads(line) for line in chunks.read_text(encoding="utf-8").splitlines()]
    assert BM25Index.build(records).search("   ") == []


def test_invalid_top_k_and_empty_corpus(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        BM25Index.build([])
    chunks = tmp_path / "chunks.jsonl"
    _write_chunks(chunks)
    records = [json.loads(line) for line in chunks.read_text(encoding="utf-8").splitlines()]
    with pytest.raises(ValueError):
        BM25Index.build(records).search("bail", top_k=0)


def test_search_excludes_zero_score_documents():
    records = [
        {"chunk_id": "c1", "doc_id": "d1", "text": "bail provision"},
        {"chunk_id": "c2", "doc_id": "d2", "text": "contract damages"},
    ]
    results = BM25Index.build(records).search("bail", top_k=10)
    assert results
    assert all(result.score > 0 for result in results)
