"""Load stage: persist dataset, metrics, processing log, and errors."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def write_json(data: Any, path: str | Path, pretty: bool = False) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file_obj:
        json.dump(
            data,
            file_obj,
            ensure_ascii=False,
            indent=2 if pretty else None,
        )


def write_processing_log(rows: list[dict[str, Any]], path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "file_id",
        "source_path",
        "file_name",
        "file_format",
        "file_size_bytes",
        "file_hash",
        "modified_at",
        "ingest_status",
        "duplicate_of",
            "processing_status",
            "extraction_status",
            "validation_status",
            "extractor_used",
            "fallback_used",
            "fallback_reason",
            "extractor_status",
            "processing_time_sec",
            "errors",
        ]
    with output_path.open("w", encoding="utf-8", newline="") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            normalized = {field: row.get(field, "") for field in fieldnames}
            if isinstance(normalized["errors"], list):
                normalized["errors"] = " | ".join(normalized["errors"])
            if isinstance(normalized["fallback_used"], bool):
                normalized["fallback_used"] = str(normalized["fallback_used"]).lower()
            writer.writerow(normalized)


def collect_errors(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "document_id": document.get("document_id"),
            "file_name": document.get("file_name"),
            "file_format": document.get("file_format"),
            "source_path": document.get("source_path"),
            "extraction_status": document.get("extraction_status"),
            "validation_status": document.get("validation_status"),
            "errors": document.get("errors", []),
        }
        for document in documents
        if document.get("errors")
    ]
