import json
from pathlib import Path

from ingestion.pipeline import build_documents, run_ingestion
from ingestion.matching import scan_judgments


def _write_pdf(path: Path, body: bytes = b"%PDF-1.4 content") -> None:
    path.write_bytes(body)


def _layout(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    raw = tmp_path / "data" / "raw"
    judgments = raw / "Suprem Court Judgements"
    metadata = judgments / "metadata"
    pdfs = judgments / "Pdfs"
    statutes = raw / "Statues"
    metadata.mkdir(parents=True)
    pdfs.mkdir()
    statutes.mkdir()
    return raw, metadata, pdfs, statutes


def test_judgment_and_statute_schema(tmp_path: Path) -> None:
    raw, metadata, pdfs, statutes = _layout(tmp_path)
    (metadata / "metadata1.txt").write_bytes(b"exact caption")
    _write_pdf(pdfs / "1.pdf")
    _write_pdf(statutes / "BNS.pdf", b"%PDF-1.7 BNS")
    _write_pdf(statutes / "BNSS2023.pdf", b"%PDF-1.6 BNSS")
    _write_pdf(statutes / "BSA.pdf", b"%PDF-1.7 BSA")

    documents, report = build_documents(raw, tmp_path)
    by_id = {doc.doc_id: doc for doc in documents}

    judgment = by_id["judgment:1"]
    assert judgment.doc_type == "judgment"
    assert judgment.pair_id == 1
    assert judgment.pdf_filename == "1.pdf"
    assert judgment.caption_text == "exact caption"
    assert judgment.source_pdf.endswith("Pdfs/1.pdf")
    assert judgment.caption_path.endswith("metadata/metadata1.txt")

    statute = by_id["statute:BNS"]
    assert statute.doc_type == "statute"
    assert statute.pair_id is None
    assert statute.caption_path is None
    assert statute.caption_text is None
    assert statute.pdf_filename == "BNS.pdf"
    assert statute.doc_id == "statute:BNS"
    assert by_id["statute:BNSS2023"].pdf_filename == "BNSS2023.pdf"

    assert report.missing_metadata == []
    assert report.bns_bsa_byte_identical is False


def test_missing_metadata_emits_null_caption_without_inventing(
    tmp_path: Path,
) -> None:
    raw, metadata, pdfs, statutes = _layout(tmp_path)
    del metadata  # unused; directory exists empty of id 25
    _write_pdf(pdfs / "25.pdf")
    _write_pdf(statutes / "BNS.pdf")
    _write_pdf(statutes / "BNSS2023.pdf")
    _write_pdf(statutes / "BSA.pdf")

    documents, report = build_documents(raw, tmp_path)
    judgment = next(doc for doc in documents if doc.doc_type == "judgment")

    assert judgment.doc_id == "judgment:25"
    assert judgment.caption_path is None
    assert judgment.caption_text is None
    assert report.missing_metadata == [25]


def test_caption_text_preserved_exactly(tmp_path: Path) -> None:
    raw, metadata, pdfs, statutes = _layout(tmp_path)
    raw_caption = "  REPORTABLE\t2024 INSC 1  \r\ntrailing"
    (metadata / "metadata1.txt").write_bytes(raw_caption.encode("utf-8"))
    _write_pdf(pdfs / "1.pdf")
    _write_pdf(statutes / "BNS.pdf")
    _write_pdf(statutes / "BNSS2023.pdf")
    _write_pdf(statutes / "BSA.pdf")

    documents, _report = build_documents(raw, tmp_path)
    judgment = next(doc for doc in documents if doc.doc_id == "judgment:1")
    assert judgment.caption_text == raw_caption


def test_unreadable_metadata_and_pdf_are_reported(tmp_path: Path) -> None:
    raw, metadata, pdfs, statutes = _layout(tmp_path)
    (metadata / "metadata1.txt").write_bytes(b"\xff\xfe not utf-8")
    (pdfs / "1.pdf").write_bytes(b"not a pdf")
    _write_pdf(statutes / "BNS.pdf")
    _write_pdf(statutes / "BNSS2023.pdf")
    _write_pdf(statutes / "BSA.pdf")

    documents, report = build_documents(raw, tmp_path)
    judgment = next(doc for doc in documents if doc.doc_id == "judgment:1")

    assert judgment.caption_text is None
    assert judgment.caption_path is not None
    assert report.unreadable_metadata_files
    assert report.unreadable_pdfs


def test_duplicate_pair_ids_are_reported_and_not_written(tmp_path: Path) -> None:
    raw, metadata, pdfs, statutes = _layout(tmp_path)
    (metadata / "metadata1.txt").write_text("a", encoding="utf-8")
    (metadata / "metadata01.txt").write_text("b", encoding="utf-8")
    _write_pdf(pdfs / "1.pdf")
    _write_pdf(statutes / "BNS.pdf")
    _write_pdf(statutes / "BNSS2023.pdf")
    _write_pdf(statutes / "BSA.pdf")

    documents, report = build_documents(raw, tmp_path)

    assert report.duplicate_pair_ids == [1]
    assert all(doc.doc_id != "judgment:1" for doc in documents)


def test_missing_statute_pdf_is_reported(tmp_path: Path) -> None:
    raw, _metadata, pdfs, statutes = _layout(tmp_path)
    _write_pdf(pdfs / "1.pdf")
    (raw / "Suprem Court Judgements" / "metadata" / "metadata1.txt").write_text(
        "c", encoding="utf-8"
    )
    _write_pdf(statutes / "BNS.pdf")
    _write_pdf(statutes / "BNSS2023.pdf")

    documents, report = build_documents(raw, tmp_path)

    assert "BSA.pdf" in report.missing_pdfs
    assert all(doc.pdf_filename != "BSA.pdf" for doc in documents)


def test_bns_bsa_byte_identity_reported_without_changing_files(
    tmp_path: Path,
) -> None:
    raw, metadata, pdfs, statutes = _layout(tmp_path)
    (metadata / "metadata1.txt").write_text("c", encoding="utf-8")
    _write_pdf(pdfs / "1.pdf")
    payload = b"%PDF-1.7 identical-bytes"
    _write_pdf(statutes / "BNS.pdf", payload)
    _write_pdf(statutes / "BNSS2023.pdf", b"%PDF-1.6 other")
    _write_pdf(statutes / "BSA.pdf", payload)

    _documents, report = build_documents(raw, tmp_path)

    assert report.bns_bsa_byte_identical is True
    assert ["BNS.pdf", "BSA.pdf"] in report.byte_identical_statute_pairs
    assert (statutes / "BNS.pdf").read_bytes() == payload
    assert (statutes / "BSA.pdf").read_bytes() == payload
    assert (statutes / "BNS.pdf").name == "BNS.pdf"
    assert (statutes / "BSA.pdf").name == "BSA.pdf"


def test_run_ingestion_writes_jsonl(tmp_path: Path) -> None:
    raw, metadata, pdfs, statutes = _layout(tmp_path)
    (metadata / "metadata1.txt").write_bytes(b"caption")
    _write_pdf(pdfs / "1.pdf")
    _write_pdf(pdfs / "2.pdf")
    _write_pdf(statutes / "BNS.pdf", b"%PDF-1.7 a")
    _write_pdf(statutes / "BNSS2023.pdf", b"%PDF-1.6 b")
    _write_pdf(statutes / "BSA.pdf", b"%PDF-1.7 c")

    output = tmp_path / "data" / "processed" / "documents.jsonl"
    report = run_ingestion(project_root=tmp_path)

    assert report.documents_written == 5
    lines = output.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 5
    first = json.loads(lines[0])
    assert first["doc_id"] == "judgment:1"
    assert first["caption_text"] == "caption"
    assert json.loads(lines[2])["doc_id"] == "statute:BNS"


def test_scan_is_used_for_missing_pdf_ids(tmp_path: Path) -> None:
    raw, metadata, pdfs, statutes = _layout(tmp_path)
    (metadata / "metadata9.txt").write_text("orphan", encoding="utf-8")
    _write_pdf(statutes / "BNS.pdf")
    _write_pdf(statutes / "BNSS2023.pdf")
    _write_pdf(statutes / "BSA.pdf")

    scan = scan_judgments(metadata, pdfs)
    _documents, report = build_documents(raw, tmp_path, scan=scan)

    assert report.missing_pdfs == ["9"]
