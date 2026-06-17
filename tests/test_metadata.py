from src.transform.difficulty_classifier import classify_difficulty
from src.transform.metadata_extractor import detect_language, extract_keywords, has_code, has_formulas
from src.transform.topic_classifier import classify_topic


def test_topic_classification_databases() -> None:
    text = "SQL запрос использует индекс таблицы PostgreSQL и транзакция фиксирует изменения."

    assert classify_topic(text) == "databases"


def test_difficulty_classification_hard() -> None:
    assert (
        classify_difficulty(
            word_count=2500,
            topic_term_count=25,
            has_formulas=True,
            has_code=False,
            average_sentence_words=28,
        )
        == "hard"
    )


def test_language_keywords_and_flags() -> None:
    text = "Автор: Иван. Python import pandas. Формула y = f(x). Анализ данных и визуализация данных."

    assert detect_language(text) == "ru"
    assert "данных" not in extract_keywords(text, "ru", top_n=5)
    assert has_code(text)
    assert has_formulas(text)

