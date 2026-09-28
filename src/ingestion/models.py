"""Normalized document records and ingestion validation report."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Document(BaseModel):
    model_config = ConfigDict(extra="forbid")

    doc_id: str
    doc_type: Literal["judgment", "statute"]
    pair_id: int | None
    source_pdf: str
    caption_path: str | None
    caption_text: str | None
    pdf_filename: str


class IngestionReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    documents_written: int
    output_path: str
    missing_metadata: list[int] = Field(default_factory=list)
    missing_pdfs: list[str] = Field(default_factory=list)
    duplicate_pair_ids: list[int] = Field(default_factory=list)
    unreadable_metadata_files: list[str] = Field(default_factory=list)
    unreadable_pdfs: list[str] = Field(default_factory=list)
    bns_bsa_byte_identical: bool | None = None
    byte_identical_statute_pairs: list[list[str]] = Field(default_factory=list)
