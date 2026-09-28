"""Filename parsing and integer pair-id matching for Supreme Court files."""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

METADATA_FILENAME = re.compile(r"^metadata(\d+)\.txt$")
JUDGMENT_PDF_FILENAME = re.compile(r"^(\d+)\.pdf$")


def parse_metadata_pair_id(filename: str) -> int | None:
    match = METADATA_FILENAME.fullmatch(filename)
    if match is None:
        return None
    return int(match.group(1))


def parse_judgment_pdf_pair_id(filename: str) -> int | None:
    match = JUDGMENT_PDF_FILENAME.fullmatch(filename)
    if match is None:
        return None
    return int(match.group(1))


@dataclass(frozen=True)
class JudgmentScan:
    metadata_by_id: dict[int, list[Path]]
    pdfs_by_id: dict[int, list[Path]]

    @property
    def duplicate_pair_ids(self) -> list[int]:
        duplicated = {
            pair_id
            for pair_id, paths in self.metadata_by_id.items()
            if len(paths) > 1
        }
        duplicated.update(
            pair_id for pair_id, paths in self.pdfs_by_id.items() if len(paths) > 1
        )
        return sorted(duplicated)

    @property
    def missing_metadata_ids(self) -> list[int]:
        return sorted(set(self.pdfs_by_id) - set(self.metadata_by_id))

    @property
    def missing_pdf_ids(self) -> list[int]:
        return sorted(set(self.metadata_by_id) - set(self.pdfs_by_id))


def scan_judgments(metadata_dir: Path, pdfs_dir: Path) -> JudgmentScan:
    """Index files by integer N. Ignores names that do not match the patterns."""
    metadata_by_id: dict[int, list[Path]] = defaultdict(list)
    pdfs_by_id: dict[int, list[Path]] = defaultdict(list)

    if metadata_dir.is_dir():
        for path in metadata_dir.iterdir():
            if not path.is_file():
                continue
            pair_id = parse_metadata_pair_id(path.name)
            if pair_id is not None:
                metadata_by_id[pair_id].append(path)

    if pdfs_dir.is_dir():
        for path in pdfs_dir.iterdir():
            if not path.is_file():
                continue
            pair_id = parse_judgment_pdf_pair_id(path.name)
            if pair_id is not None:
                pdfs_by_id[pair_id].append(path)

    for paths in metadata_by_id.values():
        paths.sort(key=lambda item: item.name)
    for paths in pdfs_by_id.values():
        paths.sort(key=lambda item: item.name)

    return JudgmentScan(
        metadata_by_id=dict(metadata_by_id),
        pdfs_by_id=dict(pdfs_by_id),
    )


def matched_pair_ids(scan: JudgmentScan) -> list[int]:
    """IDs that have exactly one PDF. Metadata may be absent."""
    duplicates = set(scan.duplicate_pair_ids)
    return sorted(
        pair_id
        for pair_id, paths in scan.pdfs_by_id.items()
        if pair_id not in duplicates and len(paths) == 1
    )
