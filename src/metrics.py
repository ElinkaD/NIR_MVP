"""Metrics for the experimental report."""

from __future__ import annotations

from collections import defaultdict
from statistics import mean
from typing import Any

COMMON_METADATA_FIELDS = (
    "title",
    "author",
    "language",
    "topic",
    "difficulty",
    "keywords",
    "word_count",
    "char_count",
)


def _is_complete(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() not in {"", "unknown"}
    if isinstance(value, list):
        return len(value) > 0
    if isinstance(value, (int, float)):
        return value > 0
    return bool(value)


def compute_metrics(
    *,
    documents: list[dict[str, Any]],
    log_rows: list[dict[str, Any]],
    total_processing_time_sec: float,
) -> dict[str, Any]:
    total_files = len(log_rows)
    skipped_duplicates = sum(1 for row in log_rows if row.get("processing_status") == "skipped_duplicate")
    processed_files = sum(1 for doc in documents if doc.get("validation_status") == "success")
    failed_files = sum(1 for doc in documents if doc.get("validation_status") != "success")
    attempted_files = processed_files + failed_files
    success_rate = processed_files / attempted_files if attempted_files else 0.0

    processing_times = [float(doc.get("processing_time_sec") or 0.0) for doc in documents]
    successful_docs = [doc for doc in documents if doc.get("validation_status") == "success"]

    formats = sorted({row.get("file_format", "unknown") for row in log_rows})
    success_rate_by_format: dict[str, float] = {}
    average_processing_time_by_format: dict[str, float] = {}
    error_count_by_format: dict[str, int] = {}
    file_format_distribution: dict[str, int] = {}

    for file_format in formats:
        format_rows = [row for row in log_rows if row.get("file_format") == file_format]
        format_docs = [doc for doc in documents if doc.get("file_format") == file_format]
        format_success = [doc for doc in format_docs if doc.get("validation_status") == "success"]
        success_rate_by_format[file_format] = len(format_success) / len(format_docs) if format_docs else 0.0
        times = [float(doc.get("processing_time_sec") or 0.0) for doc in format_docs]
        average_processing_time_by_format[file_format] = mean(times) if times else 0.0
        error_count_by_format[file_format] = sum(1 for doc in format_docs if doc.get("errors"))
        file_format_distribution[file_format] = len(format_rows)

    common_completeness_by_field: dict[str, float] = {}
    for field in COMMON_METADATA_FIELDS:
        if not documents:
            common_completeness_by_field[field] = 0.0
            continue
        common_completeness_by_field[field] = sum(1 for doc in documents if _is_complete(doc.get(field))) / len(documents)

    metadata_completeness_common = (
        mean(common_completeness_by_field.values()) if common_completeness_by_field else 0.0
    )

    format_specific_checks: list[bool] = []
    format_specific_by_field: dict[str, float] = {}
    pdf_docs = [doc for doc in documents if doc.get("file_format") == "pdf"]
    heading_docs = [doc for doc in documents if doc.get("file_format") in {"html", "docx"}]

    if pdf_docs:
        page_checks = [_is_complete(doc.get("page_count")) for doc in pdf_docs]
        format_specific_by_field["pdf.page_count"] = sum(page_checks) / len(page_checks)
        format_specific_checks.extend(page_checks)
    if heading_docs:
        heading_checks = [_is_complete(doc.get("headings")) for doc in heading_docs]
        format_specific_by_field["html_docx.headings"] = sum(heading_checks) / len(heading_checks)
        format_specific_checks.extend(heading_checks)
    if documents:
        embedded_checks = [_is_complete(doc.get("embedded_metadata")) for doc in documents]
        format_specific_by_field["embedded_metadata"] = sum(embedded_checks) / len(embedded_checks)
        format_specific_checks.extend(embedded_checks)

    metadata_completeness_format_specific = (
        sum(1 for is_complete in format_specific_checks if is_complete) / len(format_specific_checks)
        if format_specific_checks
        else 0.0
    )
    metadata_completeness_total = mean(
        [metadata_completeness_common, metadata_completeness_format_specific]
    )

    return {
        "total_files": total_files,
        "processed_files": processed_files,
        "failed_files": failed_files,
        "skipped_duplicates": skipped_duplicates,
        "success_rate": success_rate,
        "average_processing_time_sec": mean(processing_times) if processing_times else 0.0,
        "total_processing_time_sec": total_processing_time_sec,
        "files_per_second": attempted_files / total_processing_time_sec if total_processing_time_sec > 0 else 0.0,
        "average_words_per_document": mean([doc.get("word_count", 0) for doc in successful_docs])
        if successful_docs
        else 0.0,
        "metadata_completeness": metadata_completeness_total,
        "metadata_completeness_common": metadata_completeness_common,
        "metadata_completeness_format_specific": metadata_completeness_format_specific,
        "metadata_completeness_total": metadata_completeness_total,
        "metadata_completeness_by_field": common_completeness_by_field,
        "metadata_completeness_common_by_field": common_completeness_by_field,
        "metadata_completeness_format_specific_by_field": format_specific_by_field,
        "success_rate_by_format": success_rate_by_format,
        "average_processing_time_by_format": average_processing_time_by_format,
        "error_count_by_format": error_count_by_format,
        "file_format_distribution": file_format_distribution,
        "processing_time_by_document": [
            {
                "document_id": doc.get("document_id"),
                "file_name": doc.get("file_name"),
                "file_format": doc.get("file_format"),
                "processing_time_sec": doc.get("processing_time_sec", 0.0),
            }
            for doc in documents
        ],
    }


def summarize_logs_by_status(log_rows: list[dict[str, Any]]) -> dict[str, int]:
    summary: defaultdict[str, int] = defaultdict(int)
    for row in log_rows:
        summary[str(row.get("processing_status", "unknown"))] += 1
    return dict(summary)
