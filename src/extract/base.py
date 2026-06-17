"""Common extraction interface."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


@dataclass(slots=True)
class ExtractionResult:
    text: str = ""
    page_count: int | None = None
    title: str | None = None
    author: str | None = None
    headings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    extractor_used: str | None = None
    fallback_used: bool = False
    fallback_reason: str | None = None
    extractor_status: str = "success"
    extraction_status: str = "success"
    errors: list[str] = field(default_factory=list)


class BaseExtractor(Protocol):
    def extract(self, path: Path) -> ExtractionResult:
        """Extract text and metadata from a document."""
