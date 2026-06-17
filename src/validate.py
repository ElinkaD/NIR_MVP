"""Validate enriched records through Pydantic and quality checks."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from .config import VALID_DIFFICULTIES, VALID_TOPICS
from .models import DocumentRecord, model_to_dict


def validate_document(record: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    errors = list(record.get("errors") or [])
    extraction_status = record.get("extraction_status", "success")

    if extraction_status == "success" and not str(record.get("text") or "").strip():
        errors.append("Successful document must contain non-empty text")
    if record.get("file_size_bytes", 0) <= 0:
        errors.append("file_size_bytes must be greater than 0")
    if record.get("word_count", 0) < 0:
        errors.append("word_count must be non-negative")
    if record.get("char_count", 0) < 0:
        errors.append("char_count must be non-negative")
    if record.get("processing_time_sec", 0.0) < 0:
        errors.append("processing_time_sec must be non-negative")
    if record.get("topic") not in VALID_TOPICS:
        errors.append(f"topic must be one of: {sorted(VALID_TOPICS)}")
    if record.get("difficulty") not in VALID_DIFFICULTIES:
        errors.append(f"difficulty must be one of: {sorted(VALID_DIFFICULTIES)}")
    if not isinstance(record.get("keywords"), list):
        errors.append("keywords must be a list")
    if not isinstance(record.get("headings", []), list):
        errors.append("headings must be a list")
    if not isinstance(record.get("embedded_metadata", {}), dict):
        errors.append("embedded_metadata must be a dict")
    if record.get("file_format") == "pdf" and record.get("page_count") is not None and record["page_count"] <= 0:
        errors.append("page_count must be greater than 0 for PDF when detected")

    validation_status = "success" if not errors and extraction_status == "success" else "validation_failed"
    if extraction_status != "success":
        validation_status = "failed"

    normalized = {**record, "errors": errors, "validation_status": validation_status}
    try:
        model = DocumentRecord(**normalized)
        return model_to_dict(model), errors
    except ValidationError as exc:
        schema_errors = [f"Pydantic schema error: {error['loc']}: {error['msg']}" for error in exc.errors()]
        fallback = {
            **normalized,
            "validation_status": "validation_failed",
            "errors": errors + schema_errors,
        }
        model = DocumentRecord(**_coerce_minimal_record(fallback))
        return model_to_dict(model), fallback["errors"]


def _coerce_minimal_record(record: dict[str, Any]) -> dict[str, Any]:
    defaults = {
        "document_id": "unknown",
        "source_path": "",
        "file_name": "",
        "file_format": "unknown",
        "file_size_bytes": 0,
        "file_hash": "",
        "language": "unknown",
        "topic": "unknown",
        "difficulty": "easy",
        "keywords": [],
        "word_count": 0,
        "char_count": 0,
        "has_formulas": False,
        "has_code": False,
        "headings": [],
        "embedded_metadata": {},
        "extractor_used": None,
        "fallback_used": False,
        "fallback_reason": None,
        "duplicate_of": None,
        "ingest_status": "ready",
        "extractor_status": "failed",
        "text": "",
        "extraction_status": "failed",
        "validation_status": "validation_failed",
        "errors": [],
        "processing_time_sec": 0.0,
    }
    coerced = {**defaults, **record}
    if not isinstance(coerced.get("keywords"), list):
        coerced["keywords"] = []
    if not isinstance(coerced.get("headings"), list):
        coerced["headings"] = []
    if not isinstance(coerced.get("embedded_metadata"), dict):
        coerced["embedded_metadata"] = {}
    return coerced
