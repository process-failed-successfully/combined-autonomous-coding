import unittest
import tempfile
import os
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch
from shared.random_lab import RandomLabManager

class TestRandomLab(unittest.TestCase):

    def setUp(self):
        self.manager = RandomLabManager()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_file = Path(self.temp_dir) / "test.txt"
        self.temp_file.write_text("line1\nline2\nline3\nline4\nline5", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_int(self):
        # Test range
        results = self.manager.generate_int(10, 20, count=100)
        self.assertEqual(len(results), 100)
        for r in results:
            self.assertGreaterEqual(r, 10)
            self.assertLessEqual(r, 20)

    def test_float(self):
        results = self.manager.generate_float(1.0, 2.0, count=100)
        self.assertEqual(len(results), 100)
        for r in results:
            self.assertGreaterEqual(r, 1.0)
            self.assertLessEqual(r, 2.0)

    def test_string(self):
        # Test length and charset
        charset = "abc"
        results = self.manager.generate_string(10, charset, count=5)
        self.assertEqual(len(results), 5)
        for r in results:
            self.assertEqual(len(r), 10)
            for c in r:
                self.assertIn(c, charset)

        # Test predefined charsets
        res_alpha = self.manager.generate_string(5, "alpha")[0]
        import string
        for c in res_alpha:
            self.assertIn(c, string.ascii_letters)

    def test_choice(self):
        items = ["a", "b", "c"]
        results = self.manager.choice(items, count=10)
        self.assertEqual(len(results), 10)
        for r in results:
            self.assertIn(r, items)

    def test_pick_lines(self):
        # Default
        results = self.manager.pick_lines(self.temp_file, count=3)
        self.assertEqual(len(results), 3)
        possible_lines = ["line1", "line2", "line3", "line4", "line5"]
        for r in results:
            self.assertIn(r, possible_lines)

        # Unique
        results_unique = self.manager.pick_lines(self.temp_file, count=5, unique=True)
        self.assertEqual(len(results_unique), 5)
        self.assertEqual(len(set(results_unique)), 5)

        # Error if count > len with unique
        with self.assertRaises(ValueError):
            self.manager.pick_lines(self.temp_file, count=6, unique=True)

    def test_shuffle_lines(self):
        results = self.manager.shuffle_lines(self.temp_file)
        self.assertEqual(len(results), 5)
        self.assertEqual(set(results), {"line1", "line2", "line3", "line4", "line5"})
        # Order *might* be same by chance, but unlikely.
        # We just verify content preservation.

    def test_uuid(self):
        results = self.manager.generate_uuid(version=4, count=5)
        self.assertEqual(len(results), 5)
        # Verify format roughly
        import re
        uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$', re.I)
        for r in results:
            self.assertTrue(uuid_pattern.match(r))

        results_v1 = self.manager.generate_uuid(version=1, count=1)
        # v1 pattern check (time-based)
        uuid_v1_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-1[0-9a-f]{3}-[0-9a-f]{4}-[0-9a-f]{12}$', re.I)
        self.assertTrue(uuid_v1_pattern.match(results_v1[0]))

    def test_coin(self):
        results = self.manager.flip_coin(count=10)
        for r in results:
            self.assertIn(r, ["Heads", "Tails"])

    def test_dice(self):
        results = self.manager.roll_dice(sides=6, count=100)
        for r in results:
            self.assertGreaterEqual(r, 1)
            self.assertLessEqual(r, 6)

if __name__ == "__main__":
    unittest.main()
