"""Hashing helpers used by the Ingest stage."""

from __future__ import annotations

import hashlib
from pathlib import Path


def compute_sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Compute SHA256 for a file without loading it fully into memory."""

    digest = hashlib.sha256()
    with path.open("rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()

