import unittest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch
from shared.diff_lab import DiffLabManager


class TestDiffLab(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.manager = DiffLabManager()
        # Disable rich console to avoid cluttering test output and to assert calls
        self.manager.console = MagicMock()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_compare_json_identical(self):
        f1 = Path(self.temp_dir) / "1.json"
        f2 = Path(self.temp_dir) / "2.json"
        data = {"a": 1, "b": [1, 2]}
        f1.write_text(json.dumps(data))
        f2.write_text(json.dumps(data))

        # Should not trigger console.print (as it prints "Identical" to stdout using print())
        with patch('sys.stdout'):
            self.manager._compare_json(f1, f2)

        self.manager.console.print.assert_not_called()

    @patch("shared.diff_lab.HAS_RICH", True)
    def test_compare_json_diff(self):
        f1 = Path(self.temp_dir) / "1.json"
        f2 = Path(self.temp_dir) / "2.json"
        f1.write_text(json.dumps({"a": 1}))
        f2.write_text(json.dumps({"a": 2}))

        self.manager._compare_json(f1, f2)
        self.manager.console.print.assert_called()

    def test_recursive_diff(self):
        d1 = {"a": 1, "b": {"c": 3}, "d": [1, 2]}
        d2 = {"a": 1, "b": {"c": 4}, "d": [1, 3]}

        diffs = self.manager._diff_recursive(d1, d2)
        self.assertEqual(len(diffs), 2)

        # b.c changed
        mod = next((d for d in diffs if "c" in d['path']), None)
        self.assertIsNotNone(mod)
        self.assertEqual(mod['type'], 'MODIFIED')
        self.assertEqual(mod['old'], 3)
        self.assertEqual(mod['new'], 4)

        # d list changed (index 1)
        lst = next((d for d in diffs if "[1]" in d['path']), None)
        self.assertIsNotNone(lst)
        self.assertEqual(lst['type'], 'MODIFIED')
        self.assertEqual(lst['old'], 2)
        self.assertEqual(lst['new'], 3)

    def test_recursive_diff_added_removed(self):
        d1 = {"a": 1}
        d2 = {"a": 1, "b": 2}

        # Added key
        diffs = self.manager._diff_recursive(d1, d2)
        self.assertEqual(len(diffs), 1)
        self.assertEqual(diffs[0]['type'], 'ADDED')
        self.assertIn("'b'", diffs[0]['path'])

        # Removed key
        diffs = self.manager._diff_recursive(d2, d1)
        self.assertEqual(len(diffs), 1)
        self.assertEqual(diffs[0]['type'], 'REMOVED')
        self.assertIn("'b'", diffs[0]['path'])

    @patch("shared.diff_lab.HAS_RICH", True)
    def test_compare_text(self):
        f1 = Path(self.temp_dir) / "1.txt"
        f2 = Path(self.temp_dir) / "2.txt"
        f1.write_text("Hello\nWorld", encoding='utf-8')
        f2.write_text("Hello\nPython", encoding='utf-8')

        self.manager._compare_text(f1, f2)
        self.manager.console.print.assert_called()

    @patch("shared.diff_lab.HAS_PILLOW", True)
    @patch("PIL.Image.open")
    @patch("PIL.ImageChops.difference")
    def test_compare_image_diff(self, mock_diff, mock_open):
        # Setup mocks
        img1 = MagicMock()
        img2 = MagicMock()
        img1.size = (100, 100)
        img2.size = (100, 100)
        img1.mode = "RGB"
        img2.mode = "RGB"

        mock_open.side_effect = [img1, img2]

        # Mock diff result (bbox means diff)
        diff_img = MagicMock()
        diff_img.getbbox.return_value = (0, 0, 10, 10)
        mock_diff.return_value = diff_img

        f1 = Path(self.temp_dir) / "1.png"
        f2 = Path(self.temp_dir) / "2.png"
        f1.touch()
        f2.touch()

        with patch('sys.stdout'):
            self.manager._compare_image(f1, f2)

        mock_diff.assert_called()


if __name__ == "__main__":
    unittest.main()
