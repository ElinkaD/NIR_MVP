from pathlib import Path

from src.ingest import discover_documents
from src.utils.hashing import compute_sha256


def test_compute_sha256(tmp_path: Path) -> None:
    file_path = tmp_path / "sample.html"
    file_path.write_text("hello", encoding="utf-8")

    assert compute_sha256(file_path) == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"


def test_unsupported_format_ignored_and_duplicates_marked(tmp_path: Path) -> None:
    first = tmp_path / "a.html"
    duplicate = tmp_path / "b.html"
    unsupported = tmp_path / "notes.txt"
    first.write_text("<h1>SQL</h1>", encoding="utf-8")
    duplicate.write_text("<h1>SQL</h1>", encoding="utf-8")
    unsupported.write_text("ignore me", encoding="utf-8")

    registry = discover_documents(tmp_path)

    assert len(registry) == 2
    assert registry[0].ingest_status == "ready"
    assert registry[1].ingest_status == "skipped_duplicate"
    assert registry[1].duplicate_of == registry[0].file_id

