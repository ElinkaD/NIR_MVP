"""PDF extraction adapter with pdfplumber as primary tool and PyPDF2 fallback."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .base import ExtractionResult


def _metadata_value(metadata: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = metadata.get(key) or metadata.get(f"/{key}")
        if value:
            return str(value)
    return None


class PdfExtractor:
    def extract(self, path: Path) -> ExtractionResult:
        errors: list[str] = []
        primary_result = self._extract_with_pdfplumber(path, errors)
        if primary_result.text.strip():
            return primary_result

        fallback_reason = (
            "pdfplumber returned empty text, used PyPDF2"
            if not primary_result.errors
            else "; ".join(primary_result.errors)
        )
        fallback_result = self._extract_with_pypdf2(path, errors, primary_result)
        fallback_result.fallback_used = True
        fallback_result.fallback_reason = fallback_reason
        if fallback_result.text.strip():
            return fallback_result

        fallback_result.extraction_status = "failed"
        fallback_result.extractor_status = "failed"
        if "PDF text layer is empty or unavailable" not in fallback_result.errors:
            fallback_result.errors.append("PDF text layer is empty or unavailable")
        return fallback_result

    def _extract_with_pdfplumber(self, path: Path, errors: list[str]) -> ExtractionResult:
        try:
            import pdfplumber
        except Exception as exc:  # pragma: no cover - depends on optional package state
            errors.append(f"pdfplumber import failed: {exc}")
            return ExtractionResult(extraction_status="failed", errors=list(errors))

        try:
            with pdfplumber.open(path) as pdf:
                page_texts = [(page.extract_text() or "") for page in pdf.pages]
                metadata = pdf.metadata or {}
                return ExtractionResult(
                    text="\n\n".join(page_texts),
                    page_count=len(pdf.pages),
                    title=_metadata_value(metadata, "Title", "title"),
                    author=_metadata_value(metadata, "Author", "author"),
                    extractor_used="pdfplumber",
                    extractor_status="success",
                    metadata={
                        "title": _metadata_value(metadata, "Title", "title"),
                        "author": _metadata_value(metadata, "Author", "author"),
                        "subject": _metadata_value(metadata, "Subject", "subject"),
                        "creator": _metadata_value(metadata, "Creator", "creator"),
                        "producer": _metadata_value(metadata, "Producer", "producer"),
                    },
                    errors=list(errors),
                )
        except Exception as exc:
            errors.append(f"pdfplumber extraction failed: {exc}")
            return ExtractionResult(
                extractor_used="pdfplumber",
                extractor_status="failed",
                extraction_status="failed",
                errors=list(errors),
            )

    def _extract_with_pypdf2(
        self,
        path: Path,
        errors: list[str],
        previous: ExtractionResult,
    ) -> ExtractionResult:
        try:
            import PyPDF2
        except Exception as exc:  # pragma: no cover - depends on optional package state
            errors.append(f"PyPDF2 import failed: {exc}")
            previous.errors = list(errors)
            return previous

        try:
            reader = PyPDF2.PdfReader(str(path))
            page_texts = [(page.extract_text() or "") for page in reader.pages]
            raw_metadata = dict(reader.metadata or {})
            metadata = {
                "title": _metadata_value(raw_metadata, "Title", "title"),
                "author": _metadata_value(raw_metadata, "Author", "author"),
                "subject": _metadata_value(raw_metadata, "Subject", "subject"),
                "creator": _metadata_value(raw_metadata, "Creator", "creator"),
                "producer": _metadata_value(raw_metadata, "Producer", "producer"),
            }
            return ExtractionResult(
                text="\n\n".join(page_texts),
                page_count=len(reader.pages),
                title=metadata.get("title") or previous.title,
                author=metadata.get("author") or previous.author,
                extractor_used="PyPDF2",
                extractor_status="success",
                metadata={**previous.metadata, **{k: v for k, v in metadata.items() if v}},
                errors=list(errors),
            )
        except Exception as exc:
            errors.append(f"PyPDF2 extraction failed: {exc}")
            previous.errors = list(errors)
            previous.extractor_status = "failed"
            return previous
