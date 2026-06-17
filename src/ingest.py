"""Ingest stage: discover supported files, hash them, and detect duplicates."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from .config import SUPPORTED_EXTENSIONS
from .utils.hashing import compute_sha256


@dataclass(slots=True)
class FileRegistryItem:
    file_id: str
    source_path: str
    file_name: str
    file_format: str
    file_size_bytes: int
    file_hash: str
    modified_at: str
    ingest_status: str
    duplicate_of: str | None = None

    def to_dict(self) -> dict[str, str | int | None]:
        return asdict(self)


def discover_documents(input_path: str | Path) -> list[FileRegistryItem]:
    """Recursively collect supported documents and mark hash duplicates."""

    root = Path(input_path).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"Input path does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Input path is not a directory: {root}")

    registry: list[FileRegistryItem] = []
    seen_hashes: dict[str, str] = {}

    for path in sorted(root.rglob("*"), key=lambda item: (_is_duplicate_folder(item, root), str(item))):
        if not path.is_file():
            continue

        suffix = path.suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            continue

        file_hash = compute_sha256(path)
        file_id = f"doc_{len(registry) + 1:05d}"
        duplicate_of = seen_hashes.get(file_hash)
        ingest_status = "skipped_duplicate" if duplicate_of else "ready"
        if not duplicate_of:
            seen_hashes[file_hash] = file_id

        stat = path.stat()
        registry.append(
            FileRegistryItem(
                file_id=file_id,
                source_path=str(path.resolve()),
                file_name=path.name,
                file_format=SUPPORTED_EXTENSIONS[suffix],
                file_size_bytes=stat.st_size,
                file_hash=file_hash,
                modified_at=datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat(timespec="seconds"),
                ingest_status=ingest_status,
                duplicate_of=duplicate_of,
            )
        )

    return registry


def _is_duplicate_folder(path: Path, root: Path) -> bool:
    try:
        return "duplicates" in path.relative_to(root).parts
    except ValueError:
        return False
