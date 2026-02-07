"""Duplicate detection logic — classifies files as binary duplicates or diverged."""

from collections import defaultdict
from typing import Callable, Optional

from models import FileRecord, DuplicateGroup, MatchType, ScanResult
from hasher import hash_candidates


def find_duplicates(
    all_files: list[FileRecord],
    progress_callback: Optional[Callable[[int, int], None]] = None,
    cancelled: Optional[Callable[[], bool]] = None,
) -> tuple[list[DuplicateGroup], list[DuplicateGroup]]:
    """Two-pass duplicate detection.

    Pass 1: Group files by lowercase filename. Keep only groups that
            span 2+ different directory roots.
    Pass 2: Hash those candidates and classify as binary duplicate or diverged.

    Returns (binary_duplicates, diverged_files).
    """
    # --- Pass 1: Group by filename across directories ---
    by_name: dict[str, list[FileRecord]] = defaultdict(list)
    for f in all_files:
        by_name[f.filename.lower()].append(f)

    # Keep only groups spanning multiple directories
    candidates: dict[str, list[FileRecord]] = {}
    for name, files in by_name.items():
        dirs = {f.directory_root for f in files}
        if len(dirs) >= 2:
            candidates[name] = files

    # Collect all files that need hashing
    files_to_hash: list[FileRecord] = []
    for files in candidates.values():
        files_to_hash.extend(files)

    # --- Pass 2: Hash and classify ---
    hash_candidates(files_to_hash, progress_callback, cancelled)

    if cancelled and cancelled():
        return [], []

    binary_groups: list[DuplicateGroup] = []
    diverged_groups: list[DuplicateGroup] = []

    for name, files in candidates.items():
        # Sub-group by hash
        by_hash: dict[str, list[FileRecord]] = defaultdict(list)
        for f in files:
            if f.sha256:
                by_hash[f.sha256].append(f)

        # Binary duplicates: same hash, files in different directories
        for hash_val, hash_group in by_hash.items():
            dirs = {f.directory_root for f in hash_group}
            if len(dirs) >= 2:
                binary_groups.append(
                    DuplicateGroup(
                        match_type=MatchType.BINARY_DUPLICATE,
                        files=hash_group,
                        shared_name=name,
                        hash_value=hash_val,
                    )
                )

        # Diverged: same filename in multiple directories but not all share the same hash
        all_hashes = {f.sha256 for f in files if f.sha256}
        if len(all_hashes) > 1:
            diverged_groups.append(
                DuplicateGroup(
                    match_type=MatchType.DIVERGED,
                    files=files,
                    shared_name=name,
                    hash_value=None,
                )
            )

    return binary_groups, diverged_groups
