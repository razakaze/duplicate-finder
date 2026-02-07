"""Tests for formatting utilities."""

import unittest
from datetime import datetime

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.formatting import format_size, format_date, format_duration


class TestFormatSize(unittest.TestCase):
    def test_bytes(self):
        self.assertEqual(format_size(0), "0 B")
        self.assertEqual(format_size(512), "512 B")
        self.assertEqual(format_size(1023), "1023 B")

    def test_kilobytes(self):
        self.assertEqual(format_size(1024), "1.0 KB")
        self.assertEqual(format_size(1536), "1.5 KB")

    def test_megabytes(self):
        self.assertEqual(format_size(1024 * 1024), "1.0 MB")
        self.assertEqual(format_size(5 * 1024 * 1024), "5.0 MB")

    def test_gigabytes(self):
        self.assertEqual(format_size(1024 * 1024 * 1024), "1.00 GB")
        self.assertEqual(format_size(int(2.5 * 1024 * 1024 * 1024)), "2.50 GB")

    def test_negative(self):
        self.assertEqual(format_size(-1), "0 B")


class TestFormatDate(unittest.TestCase):
    def test_basic(self):
        dt = datetime(2024, 3, 15, 14, 30, 45)
        self.assertEqual(format_date(dt), "2024-03-15 14:30:45")


class TestFormatDuration(unittest.TestCase):
    def test_milliseconds(self):
        self.assertEqual(format_duration(0.05), "50ms")

    def test_seconds(self):
        self.assertEqual(format_duration(5.3), "5.3s")

    def test_minutes(self):
        self.assertEqual(format_duration(125), "2m 5s")

    def test_hours(self):
        self.assertEqual(format_duration(3661), "1h 1m")


if __name__ == "__main__":
    unittest.main()
