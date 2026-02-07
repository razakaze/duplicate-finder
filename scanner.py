"""Directory traversal — collects file metadata without reading file contents."""

import os
from pathlib import Path
from datetime import datetime
from typing import Callable, Optional

from models import FileRecord

# Fire progress callback every N files (avoids flooding the UI)
_PROGRESS_INTERVAL = 50


def scan_directory(
    root: Path,
    progress_callback: Optional[Callable[[int], None]] = None,
    cancelled: Optional[Callable[[], bool]] = None,
) -> list[FileRecord]:
    """Recursively scan a directory, collecting metadata for every file.

    Uses os.walk + os.stat for performance.
    Does NOT read file contents or compute hashes.
    Progress callback fires every ~50 files for smooth UI updates.
    """
    records: list[FileRecord] = []
    root = Path(root).resolve()
    count = 0

    for dirpath, _dirnames, filenames in os.walk(root):
        if cancelled and cancelled():
            break
        for filename in filenames:
            full_path = Path(dirpath) / filename
            try:
                stat = full_path.stat()
                records.append(
                    FileRecord(
                        path=full_path,
                        directory_root=root,
                        relative_path=str(full_path.relative_to(root)),
                        filename=filename,
                        size=stat.st_size,
                        modified=datetime.fromtimestamp(stat.st_mtime),
                    )
                )
                count += 1
                if progress_callback and count % _PROGRESS_INTERVAL == 0:
                    progress_callback(count)
            except (PermissionError, OSError):
                continue

    # Final callback with accurate total
    if progress_callback:
        progress_callback(len(records))

    return records
