"""Rule-based topic classification for the MVP."""

from __future__ import annotations

import re

from ..config import TOPIC_KEYWORDS


def _count_occurrences(text: str, phrase: str) -> int:
    phrase = phrase.lower()
    if " " in phrase or any("а" <= char <= "я" or char == "ё" for char in phrase):
        return text.count(phrase)
    return len(re.findall(rf"\b{re.escape(phrase)}\b", text))


def classify_topic(text: str, extracted_keywords: list[str] | None = None) -> str:
    lower_text = text.lower()
    keyword_text = " ".join(extracted_keywords or []).lower()
    scores: dict[str, int] = {}

    for topic, phrases in TOPIC_KEYWORDS.items():
        score = 0
        for phrase in phrases:
            score += _count_occurrences(lower_text, phrase)
            score += _count_occurrences(keyword_text, phrase)
        scores[topic] = score

    best_topic, best_score = max(scores.items(), key=lambda item: item[1])
    return best_topic if best_score > 0 else "unknown"


def count_topic_terms(text: str) -> int:
    lower_text = text.lower()
    return sum(_count_occurrences(lower_text, phrase) for phrases in TOPIC_KEYWORDS.values() for phrase in phrases)

