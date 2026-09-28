"""Document ingestion, PDF extraction, and deterministic chunking."""

from ingestion.chunking import chunk_documents
from ingestion.matching import (
    matched_pair_ids,
    parse_judgment_pdf_pair_id,
    parse_metadata_pair_id,
    scan_judgments,
)
from ingestion.models import Document, IngestionReport
from ingestion.pipeline import run_ingestion

__all__ = [
    "Document",
    "IngestionReport",
    "chunk_documents",
    "matched_pair_ids",
    "parse_judgment_pdf_pair_id",
    "parse_metadata_pair_id",
    "run_ingestion",
    "scan_judgments",
]
