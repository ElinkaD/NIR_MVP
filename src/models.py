"""Pydantic models that describe pipeline output."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class DocumentRecord(BaseModel):
    document_id: str
    source_path: str
    file_name: str
    file_format: str
    file_size_bytes: int
    file_hash: str
    title: str | None = None
    author: str | None = None
    language: str = "unknown"
    topic: str = "unknown"
    difficulty: str = "easy"
    keywords: list[str] = Field(default_factory=list)
    page_count: int | None = None
    word_count: int = 0
    char_count: int = 0
    has_formulas: bool = False
    has_code: bool = False
    headings: list[str] = Field(default_factory=list)
    embedded_metadata: dict[str, Any] = Field(default_factory=dict)
    extractor_used: str | None = None
    fallback_used: bool = False
    fallback_reason: str | None = None
    duplicate_of: str | None = None
    ingest_status: str = "ready"
    extractor_status: str = "success"
    text: str = ""
    extraction_status: str = "success"
    validation_status: str = "success"
    errors: list[str] = Field(default_factory=list)
    processing_time_sec: float = 0.0


class DatasetRecord(BaseModel):
    run_id: str
    created_at: str
    input_path: str
    total_files: int
    processed_files: int
    failed_files: int
    skipped_duplicates: int = 0
    success_rate: float
    total_processing_time_sec: float
    documents: list[DocumentRecord]


def model_to_dict(model: BaseModel) -> dict[str, Any]:
    """Return a dict for both Pydantic v1 and v2."""

    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()
