import os
import stat
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from shared.permissions_lab import PermissionsManager

class TestPermissionsManager(unittest.TestCase):
    def setUp(self):
        self.manager = PermissionsManager()

    def test_to_octal(self):
        # 000
        self.assertEqual(self.manager.to_octal(False, False, False), 0)
        # 111 (7)
        self.assertEqual(self.manager.to_octal(True, True, True), 7)
        # 101 (5)
        self.assertEqual(self.manager.to_octal(True, False, True), 5)
        # 110 (6)
        self.assertEqual(self.manager.to_octal(True, True, False), 6)

    def test_to_symbolic(self):
        self.assertEqual(self.manager.to_symbolic(True, True, True), "rwx")
        self.assertEqual(self.manager.to_symbolic(True, False, True), "r-x")
        self.assertEqual(self.manager.to_symbolic(False, False, False), "---")

    def test_from_octal(self):
        self.assertEqual(self.manager.from_octal(7), (True, True, True))
        self.assertEqual(self.manager.from_octal(5), (True, False, True))
        self.assertEqual(self.manager.from_octal(0), (False, False, False))

    def test_calculate_mode(self):
        # 755 -> 493
        self.assertEqual(self.manager.calculate_mode(7, 5, 5), 0o755)
        self.assertEqual(self.manager.calculate_mode(6, 4, 4), 0o644)

    @patch("shared.permissions_lab.Path")
    def test_get_permissions_file_not_found(self, MockPath):
        MockPath.return_value.exists.return_value = False
        res = self.manager.get_permissions("nonexistent")
        self.assertIn("error", res)

    @patch("shared.permissions_lab.Path")
    def test_get_permissions_success(self, MockPath):
        mock_path = MockPath.return_value
        mock_path.exists.return_value = True
        mock_stat = MagicMock()
        # Mock st_mode for 755 (rwxr-xr-x)
        # S_IFREG (0o100000) | 0o755
        mock_stat.st_mode = stat.S_IFREG | 0o755
        mock_path.stat.return_value = mock_stat

        res = self.manager.get_permissions("somefile")

        self.assertEqual(res["octal"], "755")
        self.assertEqual(res["symbolic"], "rwxr-xr-x")
        self.assertEqual(res["owner_digit"], 7)
        self.assertEqual(res["group_digit"], 5)
        self.assertEqual(res["other_digit"], 5)

    @patch("shared.permissions_lab.os.chmod")
    @patch("shared.permissions_lab.Path")
    def test_set_permissions_success(self, MockPath, mock_chmod):
        mock_path = MockPath.return_value
        mock_path.exists.return_value = True

        res = self.manager.set_permissions("file", "755")

        self.assertTrue(res)
        mock_chmod.assert_called_with(mock_path, 0o755)

    @patch("shared.permissions_lab.Path")
    def test_set_permissions_invalid_octal(self, MockPath):
        MockPath.return_value.exists.return_value = True
        res = self.manager.set_permissions("file", "999") # 9 is invalid octal digit in int(..., 8) but my check checks .isdigit() and len=3.
        # Wait, int("999", 8) raises ValueError.

        # My code:
        # if not octal_str.isdigit() or len(octal_str) != 3: return False
        # mode = int(octal_str, 8) -> Raises ValueError if not octal digits (0-7)
        # But I catch Exception.

        res = self.manager.set_permissions("file", "888")
        self.assertFalse(res)

if __name__ == "__main__":
    unittest.main()
