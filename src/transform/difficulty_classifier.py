"""Heuristic difficulty classification."""

from __future__ import annotations


def classify_difficulty(
    *,
    word_count: int,
    topic_term_count: int,
    has_formulas: bool,
    has_code: bool,
    average_sentence_words: float,
) -> str:
    score = 0

    if word_count >= 2000:
        score += 2
    elif word_count >= 500:
        score += 1

    if topic_term_count >= 20:
        score += 2
    elif topic_term_count >= 5:
        score += 1

    if has_formulas:
        score += 1
    if has_code:
        score += 1
    if average_sentence_words >= 25:
        score += 1

    if score >= 4:
        return "hard"
    if score >= 2:
        return "medium"
    return "easy"

