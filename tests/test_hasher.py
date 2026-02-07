"""Tests for file hashing."""

import unittest
import tempfile
import hashlib
from pathlib import Path
from datetime import datetime

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hasher import compute_sha256, hash_candidates
from models import FileRecord


class TestComputeSha256(unittest.TestCase):
    def test_known_hash(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            f.write(b"hello world")
            f.flush()
            path = Path(f.name)

        try:
            result = compute_sha256(path)
            expected = hashlib.sha256(b"hello world").hexdigest()
            self.assertEqual(result, expected)
        finally:
            path.unlink()

    def test_empty_file(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            path = Path(f.name)

        try:
            result = compute_sha256(path)
            expected = hashlib.sha256(b"").hexdigest()
            self.assertEqual(result, expected)
        finally:
            path.unlink()

    def test_nonexistent_file(self):
        result = compute_sha256(Path("C:/nonexistent_file_xyz.txt"))
        self.assertIsNone(result)

    def test_identical_files_same_hash(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "a.txt").write_bytes(b"same content")
            (root / "b.txt").write_bytes(b"same content")

            hash_a = compute_sha256(root / "a.txt")
            hash_b = compute_sha256(root / "b.txt")
            self.assertEqual(hash_a, hash_b)

    def test_different_files_different_hash(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "a.txt").write_bytes(b"content A")
            (root / "b.txt").write_bytes(b"content B")

            hash_a = compute_sha256(root / "a.txt")
            hash_b = compute_sha256(root / "b.txt")
            self.assertNotEqual(hash_a, hash_b)


class TestHashCandidates(unittest.TestCase):
    def test_hashes_records_in_place(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "test.txt").write_bytes(b"test data")

            rec = FileRecord(
                path=root / "test.txt",
                directory_root=root,
                relative_path="test.txt",
                filename="test.txt",
                size=9,
                modified=datetime(2024, 1, 1),
            )
            self.assertIsNone(rec.sha256)
            hash_candidates([rec])
            self.assertIsNotNone(rec.sha256)
            self.assertEqual(rec.sha256, hashlib.sha256(b"test data").hexdigest())

    def test_progress_callback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            records = []
            for i in range(3):
                (root / f"f{i}.txt").write_bytes(f"data{i}".encode())
                records.append(
                    FileRecord(
                        path=root / f"f{i}.txt",
                        directory_root=root,
                        relative_path=f"f{i}.txt",
                        filename=f"f{i}.txt",
                        size=5,
                        modified=datetime(2024, 1, 1),
                    )
                )

            progress_calls = []
            hash_candidates(records, progress_callback=lambda cur, tot: progress_calls.append((cur, tot)))
            # Progress is throttled (every 20 files) but always fires on the last file
            self.assertGreaterEqual(len(progress_calls), 1)
            self.assertEqual(progress_calls[-1], (3, 3))


if __name__ == "__main__":
    unittest.main()
