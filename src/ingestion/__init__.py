"""Document ingestion and normalization (no chunking or retrieval)."""

from ingestion.matching import (
    parse_judgment_pdf_pair_id,
    parse_metadata_pair_id,
    scan_judgments,
)
from ingestion.models import Document, IngestionReport
from ingestion.pipeline import run_ingestion

__all__ = [
    "Document",
    "IngestionReport",
    "parse_judgment_pdf_pair_id",
    "parse_metadata_pair_id",
    "run_ingestion",
    "scan_judgments",
]
