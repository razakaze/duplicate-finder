"""SHA-256 file hashing with chunked reading and progress reporting."""

import hashlib
from pathlib import Path
from typing import Callable, Optional

from models import FileRecord

CHUNK_SIZE = 1024 * 1024  # 1 MB


def compute_sha256(filepath: Path) -> Optional[str]:
    """Compute SHA-256 hash of a file, reading in chunks."""
    h = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    except (PermissionError, OSError):
        return None


_HASH_PROGRESS_INTERVAL = 20  # report every N files to avoid flooding UI


def hash_candidates(
    candidates: list[FileRecord],
    progress_callback: Optional[Callable[[int, int], None]] = None,
    cancelled: Optional[Callable[[], bool]] = None,
) -> None:
    """Hash a list of FileRecords in place.

    Only call this on files that actually need comparison.
    Progress callback fires every ~20 files (and always on the last file)
    to keep the UI responsive without flooding the event queue.
    """
    total = len(candidates)
    for i, record in enumerate(candidates):
        if cancelled and cancelled():
            break
        record.sha256 = compute_sha256(record.path)
        current = i + 1
        if progress_callback and (current % _HASH_PROGRESS_INTERVAL == 0 or current == total):
            progress_callback(current, total)
