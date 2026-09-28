"""Scan raw sources and write documents.jsonl. No chunking or retrieval."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ingestion.matching import JudgmentScan, matched_pair_ids, scan_judgments
from ingestion.models import Document, IngestionReport

JUDGMENTS_DIRNAME = "Suprem Court Judgements"
METADATA_DIRNAME = "metadata"
PDFS_DIRNAME = "Pdfs"
STATUTES_DIRNAME = "Statues"
STATUTE_FILENAMES = ("BNS.pdf", "BNSS2023.pdf", "BSA.pdf")
PDF_MAGIC = b"%PDF-"


def relative_posix(path: Path, root: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(root.resolve()).as_posix()
    except ValueError:
        return resolved.as_posix()


def read_caption_text(path: Path) -> str:
    """Decode metadata bytes as UTF-8 with no newline translation."""
    return path.read_bytes().decode("utf-8")


def pdf_is_readable(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            return handle.read(5) == PDF_MAGIC
    except OSError:
        return False


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _judgment_document(
    pair_id: int,
    pdf_path: Path,
    metadata_path: Path | None,
    project_root: Path,
    unreadable_metadata: list[str],
    unreadable_pdfs: list[str],
) -> Document:
    caption_text: str | None = None
    caption_rel: str | None = None
    if metadata_path is not None:
        caption_rel = relative_posix(metadata_path, project_root)
        try:
            caption_text = read_caption_text(metadata_path)
        except (OSError, UnicodeDecodeError):
            unreadable_metadata.append(caption_rel)
            caption_text = None

    pdf_rel = relative_posix(pdf_path, project_root)
    if not pdf_is_readable(pdf_path):
        unreadable_pdfs.append(pdf_rel)

    return Document(
        doc_id=f"judgment:{pair_id}",
        doc_type="judgment",
        pair_id=pair_id,
        source_pdf=pdf_rel,
        caption_path=caption_rel,
        caption_text=caption_text,
        pdf_filename=pdf_path.name,
    )


def _statute_documents(
    statutes_dir: Path,
    project_root: Path,
    missing_pdfs: list[str],
    unreadable_pdfs: list[str],
) -> tuple[list[Document], dict[str, Path]]:
    documents: list[Document] = []
    readable_paths: dict[str, Path] = {}
    for filename in STATUTE_FILENAMES:
        path = statutes_dir / filename
        if not path.is_file():
            missing_pdfs.append(filename)
            continue
        pdf_rel = relative_posix(path, project_root)
        if not pdf_is_readable(path):
            unreadable_pdfs.append(pdf_rel)
        else:
            readable_paths[filename] = path
        stem = path.stem
        documents.append(
            Document(
                doc_id=f"statute:{stem}",
                doc_type="statute",
                pair_id=None,
                source_pdf=pdf_rel,
                caption_path=None,
                caption_text=None,
                pdf_filename=filename,
            )
        )
    return documents, readable_paths


def _identical_statute_pairs(
    readable_paths: dict[str, Path],
) -> tuple[bool | None, list[list[str]]]:
    hashes: dict[str, str] = {}
    for filename, path in readable_paths.items():
        try:
            hashes[filename] = sha256_file(path)
        except OSError:
            continue

    identical: list[list[str]] = []
    names = list(hashes)
    for i, left in enumerate(names):
        for right in names[i + 1 :]:
            if hashes[left] == hashes[right]:
                identical.append([left, right])

    bns = hashes.get("BNS.pdf")
    bsa = hashes.get("BSA.pdf")
    bns_bsa: bool | None
    if bns is None or bsa is None:
        bns_bsa = None
    else:
        bns_bsa = bns == bsa
    return bns_bsa, identical


def build_documents(
    raw_root: Path,
    project_root: Path,
    scan: JudgmentScan | None = None,
) -> tuple[list[Document], IngestionReport]:
    judgments_dir = raw_root / JUDGMENTS_DIRNAME
    metadata_dir = judgments_dir / METADATA_DIRNAME
    pdfs_dir = judgments_dir / PDFS_DIRNAME
    statutes_dir = raw_root / STATUTES_DIRNAME

    if scan is None:
        scan = scan_judgments(metadata_dir, pdfs_dir)

    missing_metadata = scan.missing_metadata_ids
    duplicate_pair_ids = scan.duplicate_pair_ids
    missing_pdfs = [str(pair_id) for pair_id in scan.missing_pdf_ids]
    unreadable_metadata: list[str] = []
    unreadable_pdfs: list[str] = []

    documents: list[Document] = []
    for pair_id in matched_pair_ids(scan):
        pdf_path = scan.pdfs_by_id[pair_id][0]
        metadata_paths = scan.metadata_by_id.get(pair_id, [])
        metadata_path = metadata_paths[0] if metadata_paths else None
        documents.append(
            _judgment_document(
                pair_id,
                pdf_path,
                metadata_path,
                project_root,
                unreadable_metadata,
                unreadable_pdfs,
            )
        )

    statute_docs, readable_statutes = _statute_documents(
        statutes_dir,
        project_root,
        missing_pdfs,
        unreadable_pdfs,
    )
    documents.extend(statute_docs)
    bns_bsa, identical_pairs = _identical_statute_pairs(readable_statutes)

    report = IngestionReport(
        documents_written=0,
        output_path="",
        missing_metadata=missing_metadata,
        missing_pdfs=missing_pdfs,
        duplicate_pair_ids=duplicate_pair_ids,
        unreadable_metadata_files=unreadable_metadata,
        unreadable_pdfs=unreadable_pdfs,
        bns_bsa_byte_identical=bns_bsa,
        byte_identical_statute_pairs=identical_pairs,
    )
    return documents, report


def write_jsonl(documents: list[Document], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as handle:
        for document in documents:
            handle.write(
                json.dumps(document.model_dump(), ensure_ascii=False) + "\n"
            )


def run_ingestion(
    project_root: Path,
    raw_root: Path | None = None,
    output_path: Path | None = None,
) -> IngestionReport:
    project_root = project_root.resolve()
    if raw_root is None:
        raw_root = project_root / "data" / "raw"
    if output_path is None:
        output_path = project_root / "data" / "processed" / "documents.jsonl"

    documents, report = build_documents(raw_root, project_root)
    write_jsonl(documents, output_path)
    return report.model_copy(
        update={
            "documents_written": len(documents),
            "output_path": relative_posix(output_path, project_root),
        }
    )
