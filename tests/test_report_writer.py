"""Tests for report writer."""

import unittest
import tempfile
import json
import csv
from pathlib import Path
from datetime import datetime

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import FileRecord, DuplicateGroup, MatchType, ScanResult
from report_writer import write_csv_report, write_json_summary


class TestReportWriter(unittest.TestCase):
    def _make_result(self):
        dir_a = Path("C:/test_a")
        dir_b = Path("C:/test_b")
        files = [
            FileRecord(
                path=Path("C:/test_a/doc.txt"),
                directory_root=dir_a,
                relative_path="doc.txt",
                filename="doc.txt",
                size=1024,
                modified=datetime(2024, 1, 15),
                sha256="aaa111",
            ),
            FileRecord(
                path=Path("C:/test_b/doc.txt"),
                directory_root=dir_b,
                relative_path="doc.txt",
                filename="doc.txt",
                size=1024,
                modified=datetime(2024, 1, 15),
                sha256="aaa111",
            ),
        ]
        binary_dups = [
            DuplicateGroup(
                match_type=MatchType.BINARY_DUPLICATE,
                files=files,
                shared_name="doc.txt",
                hash_value="aaa111",
            )
        ]
        return ScanResult(
            directories=[dir_a, dir_b],
            binary_duplicates=binary_dups,
            diverged_files=[],
            scan_duration=0.1,
            hash_duration=1.5,
            total_files=2,
            files_per_directory={dir_a: 1, dir_b: 1},
        )

    def test_csv_report_creates_file(self):
        result = self._make_result()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = write_csv_report(result, Path(tmpdir))
            self.assertTrue(path.exists())
            self.assertTrue(path.name.endswith(".csv"))

            with open(path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                rows = list(reader)
            # Header + 2 data rows
            self.assertEqual(len(rows), 3)
            self.assertEqual(rows[0][0], "Group ID")

    def test_json_summary_creates_file(self):
        result = self._make_result()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = write_json_summary(result, Path(tmpdir))
            self.assertTrue(path.exists())

            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(data["total_files"], 2)
            self.assertEqual(data["binary_duplicate_groups"], 1)
            self.assertEqual(data["binary_duplicate_files"], 1)
            self.assertEqual(data["diverged_groups"], 0)

    def test_json_summary_reclaimable(self):
        result = self._make_result()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = write_json_summary(result, Path(tmpdir))
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(data["reclaimable_bytes"], 1024)


if __name__ == "__main__":
    unittest.main()
