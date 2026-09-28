from pathlib import Path

from ingestion.matching import (
    matched_pair_ids,
    parse_judgment_pdf_pair_id,
    parse_metadata_pair_id,
    scan_judgments,
)


def test_parse_pair_ids_from_filenames() -> None:
    assert parse_metadata_pair_id("metadata1.txt") == 1
    assert parse_metadata_pair_id("metadata100.txt") == 100
    assert parse_judgment_pdf_pair_id("1.pdf") == 1
    assert parse_judgment_pdf_pair_id("100.pdf") == 100


def test_parse_rejects_non_matching_names() -> None:
    assert parse_metadata_pair_id("metadata1.json") is None
    assert parse_metadata_pair_id("meta1.txt") is None
    assert parse_metadata_pair_id("1.txt") is None
    assert parse_judgment_pdf_pair_id("1.PDF") is None
    assert parse_judgment_pdf_pair_id("BNS.pdf") is None
    assert parse_judgment_pdf_pair_id("judgment-1.pdf") is None


def test_match_by_integer_n_only(tmp_path: Path) -> None:
    metadata = tmp_path / "metadata"
    pdfs = tmp_path / "Pdfs"
    metadata.mkdir()
    pdfs.mkdir()
    (metadata / "metadata1.txt").write_text("caption-one", encoding="utf-8")
    (metadata / "metadata3.txt").write_text("caption-three", encoding="utf-8")
    (pdfs / "1.pdf").write_bytes(b"%PDF-1.4 fake")
    (pdfs / "2.pdf").write_bytes(b"%PDF-1.4 fake")
    (pdfs / "3.pdf").write_bytes(b"%PDF-1.4 fake")

    scan = scan_judgments(metadata, pdfs)

    assert scan.missing_metadata_ids == [2]
    assert scan.missing_pdf_ids == []
    assert matched_pair_ids(scan) == [1, 2, 3]
    assert 1 in scan.metadata_by_id
    assert 2 not in scan.metadata_by_id
    assert scan.pdfs_by_id[2][0].name == "2.pdf"


def test_no_fuzzy_match_across_adjacent_ids(tmp_path: Path) -> None:
    metadata = tmp_path / "metadata"
    pdfs = tmp_path / "Pdfs"
    metadata.mkdir()
    pdfs.mkdir()
    (metadata / "metadata25.txt").write_text("only-25", encoding="utf-8")
    (pdfs / "26.pdf").write_bytes(b"%PDF-1.4 fake")

    scan = scan_judgments(metadata, pdfs)

    assert scan.missing_metadata_ids == [26]
    assert scan.missing_pdf_ids == [25]
    assert 25 not in scan.pdfs_by_id
    assert 26 not in scan.metadata_by_id


def test_leading_zeros_collapse_to_same_pair_id(tmp_path: Path) -> None:
    metadata = tmp_path / "metadata"
    pdfs = tmp_path / "Pdfs"
    metadata.mkdir()
    pdfs.mkdir()
    (metadata / "metadata1.txt").write_text("a", encoding="utf-8")
    (metadata / "metadata01.txt").write_text("b", encoding="utf-8")
    (pdfs / "1.pdf").write_bytes(b"%PDF-1.4 fake")

    scan = scan_judgments(metadata, pdfs)

    assert scan.duplicate_pair_ids == [1]
    assert matched_pair_ids(scan) == []
