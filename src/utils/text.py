"""Text helper functions shared by transform and validation modules."""

from __future__ import annotations

import re

WORD_RE = re.compile(r"[A-Za-zА-Яа-яЁё][A-Za-zА-Яа-яЁё0-9_-]*")
SENTENCE_SPLIT_RE = re.compile(r"[.!?。！？]+")


def tokenize_words(text: str) -> list[str]:
    return [match.group(0).lower() for match in WORD_RE.finditer(text)]


def count_words(text: str) -> int:
    return len(tokenize_words(text))


def average_sentence_length(text: str) -> float:
    sentences = [sentence.strip() for sentence in SENTENCE_SPLIT_RE.split(text) if sentence.strip()]
    if not sentences:
        return 0.0
    return count_words(text) / len(sentences)

