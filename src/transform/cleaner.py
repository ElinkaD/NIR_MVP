"""Text cleaning and normalization."""

from __future__ import annotations

import re


def clean_text(text: str) -> str:
    """Normalize whitespace and remove low-risk technical noise."""

    if not text:
        return ""

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"[\u200b\ufeff]", "", normalized)
    normalized = re.sub(r"(?im)^\s*(page|страница)\s+\d+\s*$", "", normalized)
    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = re.sub(r"[ \t]*\n[ \t]*", "\n", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()

