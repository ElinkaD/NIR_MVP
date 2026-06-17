"""Extraction adapters for supported document formats."""

from __future__ import annotations

from .base import BaseExtractor
from .docx_extractor import DocxExtractor
from .html_extractor import HtmlExtractor
from .pdf_extractor import PdfExtractor


def get_extractor(file_format: str) -> BaseExtractor:
    extractors: dict[str, BaseExtractor] = {
        "pdf": PdfExtractor(),
        "docx": DocxExtractor(),
        "html": HtmlExtractor(),
    }
    try:
        return extractors[file_format]
    except KeyError as exc:
        raise ValueError(f"Unsupported file format: {file_format}") from exc

