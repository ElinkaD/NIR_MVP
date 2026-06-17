"""Metadata enrichment for cleaned document text."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from ..config import STOP_WORDS
from ..extract.base import ExtractionResult
from ..utils.text import average_sentence_length, count_words, tokenize_words
from .difficulty_classifier import classify_difficulty
from .topic_classifier import classify_topic, count_topic_terms

FORMULA_RE = re.compile(
    r"(\\\(|\\\[|\\frac|\\sum|\\int|[∑∫αβλπ≈≤≥]|[A-Za-z]\s*=\s*[^,\n;]+|f\s*\([^)]+\))"
)
CODE_RE = re.compile(
    r"(\bimport\s+\w+|\bdef\s+\w+\s*\(|\bclass\s+\w+|\bSELECT\b|\bINSERT\b|\bUPDATE\b|"
    r"public\s+static|console\.log|#include\s*<|[{};]\s*$)",
    re.IGNORECASE | re.MULTILINE,
)
AUTHOR_PATTERNS = (
    r"(?im)^\s*(?:Автор|Выполнил|Составитель)\s*[:\-]\s*(?P<author>.+?)\s*$",
    r"(?im)^\s*(?:Author|Prepared by)\s*[:\-]\s*(?P<author>.+?)\s*$",
)


def detect_language(text: str) -> str:
    sample = text.strip()
    if len(sample) >= 20:
        try:
            from langdetect import detect

            detected = detect(sample[:5000])
            if detected in {"ru", "en"}:
                return detected
        except Exception:
            pass

    cyrillic = len(re.findall(r"[А-Яа-яЁё]", sample))
    latin = len(re.findall(r"[A-Za-z]", sample))
    if cyrillic == 0 and latin == 0:
        return "unknown"
    if cyrillic >= latin:
        return "ru"
    return "en"


def has_formulas(text: str) -> bool:
    return bool(FORMULA_RE.search(text))


def has_code(text: str) -> bool:
    return bool(CODE_RE.search(text))


def extract_author(text: str, embedded_author: str | None) -> str | None:
    if embedded_author and embedded_author.strip():
        return embedded_author.strip()

    head = "\n".join(text.splitlines()[:30])
    for pattern in AUTHOR_PATTERNS:
        match = re.search(pattern, head)
        if match:
            author = re.sub(r"\s+", " ", match.group("author")).strip(" .;,-")
            return author[:120] if author else None
    return None


def extract_title(text: str, extraction: ExtractionResult) -> str | None:
    for candidate in [extraction.title, *(extraction.headings[:1] if extraction.headings else [])]:
        if candidate and candidate.strip():
            return candidate.strip()

    for line in text.splitlines()[:10]:
        line = line.strip()
        if 5 <= len(line) <= 160:
            return line
    return None


def extract_keywords(text: str, language: str, top_n: int = 10) -> list[str]:
    if not text.strip():
        return []

    try:
        import yake

        yake_language = language if language in {"ru", "en"} else "en"
        extractor = yake.KeywordExtractor(lan=yake_language, n=1, top=top_n, dedupLim=0.9)
        keywords = [keyword for keyword, _score in extractor.extract_keywords(text)]
        cleaned = [
            keyword.strip().lower()
            for keyword in keywords
            if keyword.strip() and keyword.strip().lower() not in STOP_WORDS and len(keyword.strip()) > 2
        ]
        if cleaned:
            return list(dict.fromkeys(cleaned))[:top_n]
    except Exception:
        pass

    tokens = [
        token
        for token in tokenize_words(text)
        if len(token) > 2 and token not in STOP_WORDS and not token.isdigit()
    ]
    return [word for word, _count in Counter(tokens).most_common(top_n)]


def enrich_metadata(
    *,
    text: str,
    extraction: ExtractionResult,
    file_info: dict[str, Any],
) -> dict[str, Any]:
    language = detect_language(text)
    keywords = extract_keywords(text, language)
    formula_flag = has_formulas(text)
    code_flag = has_code(text)
    words = count_words(text)
    chars = len(text)
    topic_terms = count_topic_terms(text)
    topic = classify_topic(text, keywords)
    difficulty = classify_difficulty(
        word_count=words,
        topic_term_count=topic_terms,
        has_formulas=formula_flag,
        has_code=code_flag,
        average_sentence_words=average_sentence_length(text),
    )

    return {
        "title": extract_title(text, extraction),
        "author": extract_author(text, extraction.author),
        "language": language,
        "topic": topic,
        "difficulty": difficulty,
        "keywords": keywords,
        "page_count": extraction.page_count,
        "word_count": words,
        "char_count": chars,
        "has_formulas": formula_flag,
        "has_code": code_flag,
        "file_format": file_info["file_format"],
        "file_size_bytes": file_info["file_size_bytes"],
        "file_hash": file_info["file_hash"],
        "source_path": file_info["source_path"],
    }
