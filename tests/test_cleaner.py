from src.transform.cleaner import clean_text


def test_clean_text_normalizes_spaces_and_blank_lines() -> None:
    raw = "  Page 1\n\n\nТекст   с    пробелами.\r\n\r\nСледующая строка.  "

    assert clean_text(raw) == "Текст с пробелами.\n\nСледующая строка."

