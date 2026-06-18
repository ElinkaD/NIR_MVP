import argparse
from pathlib import Path

from src.main import run_pipeline


def test_bad_file_is_preserved_as_failed_and_duplicate_is_skipped(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    input_dir.mkdir()

    original = input_dir / "a.html"
    duplicate = input_dir / "b_duplicate.html"
    original.write_text("<html><title>ML</title><body><h1>ML</h1>model training regression</body></html>", encoding="utf-8")
    duplicate.write_text(original.read_text(encoding="utf-8"), encoding="utf-8")
    (input_dir / "bad.pdf").write_text("this is not a pdf", encoding="utf-8")

    args = argparse.Namespace(
        input=str(input_dir),
        output=str(tmp_path / "dataset.json"),
        metrics_output=str(tmp_path / "metrics.json"),
        log_output=str(tmp_path / "processing_log.csv"),
        errors_output=str(tmp_path / "errors.json"),
        pretty=True,
        limit=None,
    )

    dataset, metrics, log_rows = run_pipeline(args)

    assert dataset["total_files"] == 3
    assert metrics["processed_files"] == 1
    assert metrics["failed_files"] == 1
    assert metrics["skipped_duplicates"] == 1

    duplicate_rows = [row for row in log_rows if row["processing_status"] == "skipped_duplicate"]
    assert len(duplicate_rows) == 1
    assert duplicate_rows[0]["duplicate_of"] == "doc_00001"

    failed_docs = [doc for doc in dataset["documents"] if doc["file_name"] == "bad.pdf"]
    assert len(failed_docs) == 1
    assert failed_docs[0]["extraction_status"] == "failed"
    assert failed_docs[0]["validation_status"] == "failed"
    assert failed_docs[0]["errors"]
    assert failed_docs[0]["extractor_status"] == "failed"
