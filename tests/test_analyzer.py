"""Tests for duplicate detection analyzer."""

import unittest
import tempfile
from pathlib import Path
from datetime import datetime

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import FileRecord, MatchType
from analyzer import find_duplicates


class TestFindDuplicates(unittest.TestCase):
    def _create_test_dirs(self, tmpdir):
        """Create two directories with test files and return FileRecords."""
        root = Path(tmpdir)
        dir_a = root / "dir_a"
        dir_b = root / "dir_b"
        dir_a.mkdir()
        dir_b.mkdir()
        return dir_a, dir_b

    def test_binary_duplicates(self):
        """Two identical files in different directories -> binary duplicate."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dir_a, dir_b = self._create_test_dirs(tmpdir)

            (dir_a / "file.txt").write_bytes(b"same content")
            (dir_b / "file.txt").write_bytes(b"same content")

            records = [
                FileRecord(
                    path=dir_a / "file.txt",
                    directory_root=dir_a,
                    relative_path="file.txt",
                    filename="file.txt",
                    size=12,
                    modified=datetime(2024, 1, 1),
                ),
                FileRecord(
                    path=dir_b / "file.txt",
                    directory_root=dir_b,
                    relative_path="file.txt",
                    filename="file.txt",
                    size=12,
                    modified=datetime(2024, 1, 1),
                ),
            ]

            binary, diverged = find_duplicates(records)
            self.assertEqual(len(binary), 1)
            self.assertEqual(len(diverged), 0)
            self.assertEqual(binary[0].match_type, MatchType.BINARY_DUPLICATE)
            self.assertEqual(len(binary[0].files), 2)

    def test_diverged_files(self):
        """Same filename, different content -> diverged."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dir_a, dir_b = self._create_test_dirs(tmpdir)

            (dir_a / "file.txt").write_bytes(b"version A")
            (dir_b / "file.txt").write_bytes(b"version B - edited")

            records = [
                FileRecord(
                    path=dir_a / "file.txt",
                    directory_root=dir_a,
                    relative_path="file.txt",
                    filename="file.txt",
                    size=9,
                    modified=datetime(2024, 1, 1),
                ),
                FileRecord(
                    path=dir_b / "file.txt",
                    directory_root=dir_b,
                    relative_path="file.txt",
                    filename="file.txt",
                    size=18,
                    modified=datetime(2024, 6, 1),
                ),
            ]

            binary, diverged = find_duplicates(records)
            self.assertEqual(len(binary), 0)
            self.assertEqual(len(diverged), 1)
            self.assertEqual(diverged[0].match_type, MatchType.DIVERGED)

    def test_no_duplicates_different_names(self):
        """Different filenames -> no duplicates."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dir_a, dir_b = self._create_test_dirs(tmpdir)

            (dir_a / "file_a.txt").write_bytes(b"content")
            (dir_b / "file_b.txt").write_bytes(b"content")

            records = [
                FileRecord(
                    path=dir_a / "file_a.txt",
                    directory_root=dir_a,
                    relative_path="file_a.txt",
                    filename="file_a.txt",
                    size=7,
                    modified=datetime(2024, 1, 1),
                ),
                FileRecord(
                    path=dir_b / "file_b.txt",
                    directory_root=dir_b,
                    relative_path="file_b.txt",
                    filename="file_b.txt",
                    size=7,
                    modified=datetime(2024, 1, 1),
                ),
            ]

            binary, diverged = find_duplicates(records)
            self.assertEqual(len(binary), 0)
            self.assertEqual(len(diverged), 0)

    def test_same_name_same_directory_not_duplicate(self):
        """Files with same name in same directory root -> not considered duplicate."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dir_a = Path(tmpdir) / "dir_a"
            dir_a.mkdir()
            sub = dir_a / "subdir"
            sub.mkdir()

            (dir_a / "file.txt").write_bytes(b"content")
            (sub / "file.txt").write_bytes(b"content")

            records = [
                FileRecord(
                    path=dir_a / "file.txt",
                    directory_root=dir_a,
                    relative_path="file.txt",
                    filename="file.txt",
                    size=7,
                    modified=datetime(2024, 1, 1),
                ),
                FileRecord(
                    path=sub / "file.txt",
                    directory_root=dir_a,
                    relative_path="subdir/file.txt",
                    filename="file.txt",
                    size=7,
                    modified=datetime(2024, 1, 1),
                ),
            ]

            binary, diverged = find_duplicates(records)
            # Only one directory root, so no cross-directory duplicates
            self.assertEqual(len(binary), 0)
            self.assertEqual(len(diverged), 0)

    def test_case_insensitive_matching(self):
        """Filenames differing only in case should match on Windows."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dir_a, dir_b = self._create_test_dirs(tmpdir)

            (dir_a / "File.TXT").write_bytes(b"same")
            (dir_b / "file.txt").write_bytes(b"same")

            records = [
                FileRecord(
                    path=dir_a / "File.TXT",
                    directory_root=dir_a,
                    relative_path="File.TXT",
                    filename="File.TXT",
                    size=4,
                    modified=datetime(2024, 1, 1),
                ),
                FileRecord(
                    path=dir_b / "file.txt",
                    directory_root=dir_b,
                    relative_path="file.txt",
                    filename="file.txt",
                    size=4,
                    modified=datetime(2024, 1, 1),
                ),
            ]

            binary, diverged = find_duplicates(records)
            self.assertEqual(len(binary), 1)

    def test_three_directories_mixed(self):
        """Binary dup in A+B, diverged copy in C -> both groups found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            dir_a = root / "a"
            dir_b = root / "b"
            dir_c = root / "c"
            dir_a.mkdir()
            dir_b.mkdir()
            dir_c.mkdir()

            (dir_a / "doc.txt").write_bytes(b"original")
            (dir_b / "doc.txt").write_bytes(b"original")
            (dir_c / "doc.txt").write_bytes(b"edited version")

            records = [
                FileRecord(
                    path=dir_a / "doc.txt",
                    directory_root=dir_a,
                    relative_path="doc.txt",
                    filename="doc.txt",
                    size=8,
                    modified=datetime(2024, 1, 1),
                ),
                FileRecord(
                    path=dir_b / "doc.txt",
                    directory_root=dir_b,
                    relative_path="doc.txt",
                    filename="doc.txt",
                    size=8,
                    modified=datetime(2024, 1, 1),
                ),
                FileRecord(
                    path=dir_c / "doc.txt",
                    directory_root=dir_c,
                    relative_path="doc.txt",
                    filename="doc.txt",
                    size=14,
                    modified=datetime(2024, 6, 1),
                ),
            ]

            binary, diverged = find_duplicates(records)
            # A and B are binary duplicates
            self.assertEqual(len(binary), 1)
            self.assertEqual(len(binary[0].files), 2)
            # All three are diverged (different hashes exist)
            self.assertEqual(len(diverged), 1)
            self.assertEqual(len(diverged[0].files), 3)

    def test_empty_input(self):
        binary, diverged = find_duplicates([])
        self.assertEqual(len(binary), 0)
        self.assertEqual(len(diverged), 0)


if __name__ == "__main__":
    unittest.main()
