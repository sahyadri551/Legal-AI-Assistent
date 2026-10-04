import json
from pathlib import Path

import pytest

from ingestion.chunking import chunk_documents


def test_chunk_documents_preserves_metadata_and_overlap(tmp_path: Path) -> None:
    source = tmp_path / "documents.jsonl"
    output = tmp_path / "chunks.jsonl"
    text = "one two three four five six seven eight nine ten"
    source.write_text(
        json.dumps(
            {
                "doc_id": "judgment:1",
                "doc_type": "judgment",
                "pair_id": 1,
                "source_pdf": "data/raw/1.pdf",
                "caption_path": "data/raw/metadata1.txt",
                "caption_text": "caption",
                "pdf_filename": "1.pdf",
                "text": text,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = chunk_documents(source, output, max_chars=18, overlap_chars=6)
    rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]

    assert report["documents"] == 1
    assert report["chunks"] >= 2
    assert rows[0]["doc_id"] == "judgment:1"
    assert rows[0]["chunk_id"] == "judgment:1:0"
    assert rows[0]["caption_text"] == "caption"
    assert any(set(row["text"].split()) & set(rows[0]["text"].split()) for row in rows[1:])


def test_chunking_empty_text(tmp_path: Path) -> None:
    source = tmp_path / "documents.jsonl"
    output = tmp_path / "chunks.jsonl"
    source.write_text(
        json.dumps(
            {
                "doc_id": "statute:BNS",
                "doc_type": "statute",
                "pair_id": None,
                "source_pdf": "BNS.pdf",
                "caption_path": None,
                "caption_text": None,
                "pdf_filename": "BNS.pdf",
                "text": "",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = chunk_documents(source, output)
    assert report["chunks"] == 0
    assert report["zero_text_documents"] == 1


@pytest.mark.parametrize(
    ("max_chars", "overlap_chars"),
    [(0, 0), (10, 10), (10, 11)],
)
def test_invalid_chunk_config(tmp_path: Path, max_chars: int, overlap_chars: int) -> None:
    source = tmp_path / "documents.jsonl"
    output = tmp_path / "chunks.jsonl"
    source.write_text("", encoding="utf-8")

    with pytest.raises(ValueError):
        chunk_documents(source, output, max_chars, overlap_chars)


def test_public_chunk_text_matches_private_helper():
    text = "one two three four five six"
    assert chunk_text(text, max_chars=10, overlap_chars=2) == _chunk_text(text, 10, 2)


# Backward-compatible alias for existing integrations.
_chunk_text = chunk_text
