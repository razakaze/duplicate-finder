"""Tests for data models."""

import unittest
from pathlib import Path
from datetime import datetime

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import FileRecord, DuplicateGroup, MatchType, ScanResult


class TestFileRecord(unittest.TestCase):
    def _make_record(self, **kwargs):
        defaults = {
            "path": Path("C:/a/b/file.txt"),
            "directory_root": Path("C:/a"),
            "relative_path": "b/file.txt",
            "filename": "file.txt",
            "size": 1024,
            "modified": datetime(2024, 1, 15, 12, 0, 0),
        }
        defaults.update(kwargs)
        return FileRecord(**defaults)

    def test_directory_label(self):
        rec = self._make_record(directory_root=Path("C:/my_drive"))
        self.assertEqual(rec.directory_label, "C:\\my_drive")

    def test_sha256_default_none(self):
        rec = self._make_record()
        self.assertIsNone(rec.sha256)


class TestDuplicateGroup(unittest.TestCase):
    def _make_group(self, match_type=MatchType.BINARY_DUPLICATE, sizes=None, dates=None):
        sizes = sizes or [1024, 1024]
        dates = dates or [datetime(2024, 1, 1), datetime(2024, 6, 1)]
        files = []
        for i, (size, dt) in enumerate(zip(sizes, dates)):
            files.append(
                FileRecord(
                    path=Path(f"C:/dir{i}/file.txt"),
                    directory_root=Path(f"C:/dir{i}"),
                    relative_path="file.txt",
                    filename="file.txt",
                    size=size,
                    modified=dt,
                )
            )
        return DuplicateGroup(
            match_type=match_type,
            files=files,
            shared_name="file.txt",
            hash_value="abc123" if match_type == MatchType.BINARY_DUPLICATE else None,
        )

    def test_wasted_bytes_binary(self):
        group = self._make_group(
            match_type=MatchType.BINARY_DUPLICATE,
            sizes=[2048, 2048, 2048],
            dates=[datetime(2024, 1, 1), datetime(2024, 2, 1), datetime(2024, 3, 1)],
        )
        # 2 extra copies * 2048 bytes
        self.assertEqual(group.wasted_bytes, 2048 * 2)

    def test_wasted_bytes_diverged_is_zero(self):
        group = self._make_group(match_type=MatchType.DIVERGED, sizes=[1024, 2048])
        self.assertEqual(group.wasted_bytes, 0)

    def test_newest_file(self):
        group = self._make_group(dates=[datetime(2024, 1, 1), datetime(2024, 6, 1)])
        self.assertEqual(group.newest_file.modified, datetime(2024, 6, 1))

    def test_oldest_file(self):
        group = self._make_group(dates=[datetime(2024, 1, 1), datetime(2024, 6, 1)])
        self.assertEqual(group.oldest_file.modified, datetime(2024, 1, 1))

    def test_empty_group(self):
        group = DuplicateGroup(
            match_type=MatchType.BINARY_DUPLICATE,
            files=[],
            shared_name="empty.txt",
        )
        self.assertEqual(group.wasted_bytes, 0)
        self.assertIsNone(group.newest_file)
        self.assertIsNone(group.oldest_file)


class TestScanResult(unittest.TestCase):
    def _make_result(self):
        dir_a = Path("C:/a")
        dir_b = Path("C:/b")
        files = [
            FileRecord(
                path=Path("C:/a/f1.txt"),
                directory_root=dir_a,
                relative_path="f1.txt",
                filename="f1.txt",
                size=100,
                modified=datetime(2024, 1, 1),
            ),
            FileRecord(
                path=Path("C:/a/f2.txt"),
                directory_root=dir_a,
                relative_path="f2.txt",
                filename="f2.txt",
                size=200,
                modified=datetime(2024, 2, 1),
            ),
            FileRecord(
                path=Path("C:/b/f1.txt"),
                directory_root=dir_b,
                relative_path="f1.txt",
                filename="f1.txt",
                size=100,
                modified=datetime(2024, 1, 1),
            ),
        ]
        binary_dups = [
            DuplicateGroup(
                match_type=MatchType.BINARY_DUPLICATE,
                files=[files[0], files[2]],
                shared_name="f1.txt",
                hash_value="hash1",
            )
        ]
        return ScanResult(
            directories=[dir_a, dir_b],
            binary_duplicates=binary_dups,
            diverged_files=[],
            scan_duration=0.5,
            hash_duration=2.0,
            total_files=3,
            files_per_directory={dir_a: 2, dir_b: 1},
        )

    def test_total_files(self):
        result = self._make_result()
        self.assertEqual(result.total_files, 3)

    def test_files_per_directory(self):
        result = self._make_result()
        fpd = result.files_per_directory
        self.assertEqual(fpd[Path("C:/a")], 2)
        self.assertEqual(fpd[Path("C:/b")], 1)

    def test_total_reclaimable_bytes(self):
        result = self._make_result()
        # 1 binary duplicate group with file size 100, 1 extra copy
        self.assertEqual(result.total_reclaimable_bytes, 100)

    def test_total_binary_duplicate_count(self):
        result = self._make_result()
        self.assertEqual(result.total_binary_duplicate_count, 1)


if __name__ == "__main__":
    unittest.main()
