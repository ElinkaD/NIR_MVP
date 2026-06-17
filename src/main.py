"""Command-line entrypoint for the local ETL pipeline."""

from __future__ import annotations

import argparse
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .extract import get_extractor
from .extract.base import ExtractionResult
from .ingest import FileRegistryItem, discover_documents
from .load import collect_errors, write_json, write_processing_log
from .metrics import compute_metrics
from .models import DatasetRecord, model_to_dict
from .transform.cleaner import clean_text
from .transform.metadata_extractor import enrich_metadata
from .validate import validate_document


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ETL MVP for educational PDF/DOCX/HTML materials.")
    parser.add_argument("--input", default="data/input", help="Input directory with PDF/DOCX/HTML files.")
    parser.add_argument("--output", default="data/output/dataset.json", help="Output dataset JSON path.")
    parser.add_argument("--metrics-output", default="data/output/metrics.json", help="Output metrics JSON path.")
    parser.add_argument("--log-output", default="data/output/processing_log.csv", help="Output processing log CSV path.")
    parser.add_argument("--errors-output", default="data/output/errors.json", help="Output errors JSON path.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON files.")
    parser.add_argument("--limit", type=int, default=None, help="Process only first N discovered non-duplicate files.")
    return parser.parse_args()


def process_document(item: FileRegistryItem) -> dict[str, Any]:
    start = time.perf_counter()
    extraction = ExtractionResult(extraction_status="failed", errors=["Document was not processed"])

    try:
        extractor = get_extractor(item.file_format)
        extraction = extractor.extract(Path(item.source_path))
    except Exception as exc:
        extraction = ExtractionResult(extraction_status="failed", errors=[f"Extractor crashed: {exc}"])

    cleaned_text = clean_text(extraction.text)
    file_info = item.to_dict()
    enriched = enrich_metadata(text=cleaned_text, extraction=extraction, file_info=file_info)
    processing_time = time.perf_counter() - start

    record = {
        "document_id": item.file_id,
        "source_path": item.source_path,
        "file_name": item.file_name,
        "file_format": item.file_format,
        "file_size_bytes": item.file_size_bytes,
        "file_hash": item.file_hash,
        "duplicate_of": item.duplicate_of,
        "ingest_status": item.ingest_status,
        **enriched,
        "headings": extraction.headings,
        "embedded_metadata": extraction.metadata,
        "extractor_used": extraction.extractor_used,
        "fallback_used": extraction.fallback_used,
        "fallback_reason": extraction.fallback_reason,
        "extractor_status": extraction.extractor_status,
        "text": cleaned_text,
        "extraction_status": extraction.extraction_status,
        "validation_status": "pending",
        "errors": extraction.errors,
        "processing_time_sec": round(processing_time, 6),
    }
    validated, _errors = validate_document(record)
    return validated


def build_log_row(item: FileRegistryItem, document: dict[str, Any] | None = None) -> dict[str, Any]:
    row = item.to_dict()
    if document is None:
        return {
            **row,
            "processing_status": item.ingest_status,
            "extraction_status": "skipped",
            "validation_status": "skipped",
            "extractor_used": "",
            "fallback_used": False,
            "fallback_reason": "",
            "extractor_status": "skipped",
            "processing_time_sec": 0.0,
            "errors": [f"Duplicate of {item.duplicate_of}"] if item.duplicate_of else [],
        }

    validation_status = document.get("validation_status", "failed")
    if validation_status == "success":
        processing_status = "success"
    elif validation_status == "validation_failed":
        processing_status = "validation_failed"
    else:
        processing_status = "failed"

    return {
        **row,
        "processing_status": processing_status,
        "extraction_status": document.get("extraction_status", "failed"),
        "validation_status": validation_status,
        "extractor_used": document.get("extractor_used") or "",
        "fallback_used": document.get("fallback_used", False),
        "fallback_reason": document.get("fallback_reason") or "",
        "extractor_status": document.get("extractor_status", document.get("extraction_status", "failed")),
        "processing_time_sec": document.get("processing_time_sec", 0.0),
        "errors": document.get("errors", []),
    }


def run_pipeline(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    run_id = str(uuid.uuid4())
    run_start = time.perf_counter()
    input_path = str(Path(args.input).expanduser().resolve())

    registry = discover_documents(args.input)
    documents: list[dict[str, Any]] = []
    log_rows: list[dict[str, Any]] = []
    processed_attempts = 0

    print(f"Found supported files: {len(registry)}")

    for item in registry:
        if item.ingest_status == "skipped_duplicate":
            log_rows.append(build_log_row(item))
            print(f"[skip duplicate] {item.file_name} -> {item.duplicate_of}")
            continue

        if args.limit is not None and processed_attempts >= args.limit:
            row = item.to_dict()
            log_rows.append(
                {
                    **row,
                    "processing_status": "skipped_limit",
                    "extraction_status": "skipped",
                    "validation_status": "skipped",
                    "processing_time_sec": 0.0,
                    "errors": ["Skipped by --limit"],
                }
            )
            continue

        processed_attempts += 1
        document = process_document(item)
        documents.append(document)
        log_rows.append(build_log_row(item, document))
        print(f"[{document['validation_status']}] {item.file_name} ({document['processing_time_sec']:.3f}s)")

    total_processing_time = round(time.perf_counter() - run_start, 6)
    metrics = compute_metrics(
        documents=documents,
        log_rows=log_rows,
        total_processing_time_sec=total_processing_time,
    )

    dataset = DatasetRecord(
        run_id=run_id,
        created_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        input_path=input_path,
        total_files=metrics["total_files"],
        processed_files=metrics["processed_files"],
        failed_files=metrics["failed_files"],
        skipped_duplicates=metrics["skipped_duplicates"],
        success_rate=metrics["success_rate"],
        total_processing_time_sec=total_processing_time,
        documents=documents,
    )
    return model_to_dict(dataset), metrics | {"run_id": run_id, "created_at": dataset.created_at}, log_rows


def main() -> None:
    args = parse_args()
    dataset, metrics, log_rows = run_pipeline(args)

    write_json(dataset, args.output, pretty=args.pretty)
    write_json(metrics, args.metrics_output, pretty=True)
    write_json(collect_errors(dataset["documents"]), args.errors_output, pretty=True)
    write_processing_log(log_rows, args.log_output)

    print("\nSummary")
    print(f"Run ID: {dataset['run_id']}")
    print(f"Total files: {dataset['total_files']}")
    print(f"Processed files: {dataset['processed_files']}")
    print(f"Failed files: {dataset['failed_files']}")
    print(f"Skipped duplicates: {dataset['skipped_duplicates']}")
    print(f"Success rate: {dataset['success_rate']:.2%}")
    print(f"Dataset: {args.output}")
    print(f"Metrics: {args.metrics_output}")
    print(f"Log: {args.log_output}")
    print(f"Errors: {args.errors_output}")


if __name__ == "__main__":
    main()
