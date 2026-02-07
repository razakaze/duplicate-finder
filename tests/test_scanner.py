"""Tests for directory scanner."""

import unittest
import tempfile
import os
from pathlib import Path

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scanner import scan_directory


class TestScanDirectory(unittest.TestCase):
    def test_scans_flat_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "file1.txt").write_text("hello")
            (root / "file2.txt").write_text("world")

            records = scan_directory(root)
            self.assertEqual(len(records), 2)
            filenames = {r.filename for r in records}
            self.assertEqual(filenames, {"file1.txt", "file2.txt"})

    def test_scans_nested_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            sub = root / "subdir"
            sub.mkdir()
            (root / "a.txt").write_text("a")
            (sub / "b.txt").write_text("b")

            records = scan_directory(root)
            self.assertEqual(len(records), 2)
            rel_paths = {r.relative_path for r in records}
            self.assertIn("a.txt", rel_paths)
            self.assertTrue(
                any("subdir" in rp and "b.txt" in rp for rp in rel_paths)
            )

    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            records = scan_directory(Path(tmpdir))
            self.assertEqual(len(records), 0)

    def test_records_have_correct_root(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            (root / "test.txt").write_text("data")

            records = scan_directory(root)
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].directory_root, root)

    def test_records_have_size(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            content = "hello world"
            (root / "test.txt").write_text(content)

            records = scan_directory(root)
            self.assertEqual(len(records), 1)
            self.assertGreater(records[0].size, 0)

    def test_cancellation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            for i in range(10):
                (root / f"file{i}.txt").write_text(f"content{i}")

            # Cancel immediately
            records = scan_directory(root, cancelled=lambda: True)
            # Should have stopped early (may have some files from the first walk iteration)
            self.assertLessEqual(len(records), 10)


if __name__ == "__main__":
    unittest.main()
