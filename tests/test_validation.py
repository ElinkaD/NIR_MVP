from src.validate import validate_document


def _base_record() -> dict:
    return {
        "document_id": "doc_00001",
        "source_path": "/tmp/a.html",
        "file_name": "a.html",
        "file_format": "html",
        "file_size_bytes": 10,
        "file_hash": "abc",
        "title": "Title",
        "author": None,
        "language": "en",
        "topic": "programming",
        "difficulty": "easy",
        "keywords": ["python"],
        "page_count": None,
        "word_count": 3,
        "char_count": 18,
        "has_formulas": False,
        "has_code": True,
        "text": "Python code sample",
        "extraction_status": "success",
        "validation_status": "pending",
        "errors": [],
        "processing_time_sec": 0.01,
    }


def test_validate_successful_document() -> None:
    validated, errors = validate_document(_base_record())

    assert errors == []
    assert validated["validation_status"] == "success"


def test_validate_failed_document_is_preserved() -> None:
    record = _base_record()
    record["text"] = ""
    record["extraction_status"] = "failed"
    record["errors"] = ["extract failed"]

    validated, errors = validate_document(record)

    assert validated["validation_status"] == "failed"
    assert "extract failed" in errors

