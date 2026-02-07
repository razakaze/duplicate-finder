"""Data models for the Duplicate File Finder."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from datetime import datetime
from typing import Optional


class MatchType(Enum):
    BINARY_DUPLICATE = "binary_duplicate"
    DIVERGED = "diverged"


@dataclass
class FileRecord:
    path: Path
    directory_root: Path
    relative_path: str
    filename: str
    size: int
    modified: datetime
    sha256: Optional[str] = None

    @property
    def directory_label(self) -> str:
        return str(self.directory_root)


@dataclass
class DuplicateGroup:
    match_type: MatchType
    files: list[FileRecord]
    shared_name: str
    hash_value: Optional[str] = None

    @property
    def wasted_bytes(self) -> int:
        if self.match_type == MatchType.BINARY_DUPLICATE and self.files:
            return self.files[0].size * (len(self.files) - 1)
        return 0

    @property
    def newest_file(self) -> Optional[FileRecord]:
        if not self.files:
            return None
        return max(self.files, key=lambda f: f.modified)

    @property
    def oldest_file(self) -> Optional[FileRecord]:
        if not self.files:
            return None
        return min(self.files, key=lambda f: f.modified)


@dataclass
class ScanResult:
    directories: list[Path]
    binary_duplicates: list[DuplicateGroup]
    diverged_files: list[DuplicateGroup]
    scan_duration: float = 0.0
    hash_duration: float = 0.0
    total_files: int = 0
    files_per_directory: dict[Path, int] = field(default_factory=dict)
    total_size_per_directory: dict[Path, int] = field(default_factory=dict)

    @property
    def total_reclaimable_bytes(self) -> int:
        return sum(g.wasted_bytes for g in self.binary_duplicates)

    @property
    def total_binary_duplicate_count(self) -> int:
        return sum(len(g.files) - 1 for g in self.binary_duplicates)
