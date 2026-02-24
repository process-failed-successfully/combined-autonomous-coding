import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import json
import sys
import shutil

from shared.clipboard_lab import ClipboardManager

class TestClipboardManager(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("test_project_dir")
        self.project_dir.mkdir(exist_ok=True)
        self.manager = ClipboardManager(self.project_dir)

    def tearDown(self):
        if self.project_dir.exists():
            shutil.rmtree(self.project_dir)

    @patch("shared.clipboard_lab.HAS_PYPERCLIP", False)
    @patch("shared.clipboard_lab.sys.platform", "darwin")
    @patch("shared.clipboard_lab.subprocess.run")
    def test_copy_system_fallback_mac(self, mock_run):
        # Test copy using pbcopy
        mock_run.return_value.returncode = 0

        success = self.manager.copy_to_system("hello")
        self.assertTrue(success)
        mock_run.assert_called_with(["pbcopy"], input=b"hello", check=True)

        # Verify history
        history = self.manager.get_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["text"], "hello")

    @patch("shared.clipboard_lab.HAS_PYPERCLIP", False)
    @patch("shared.clipboard_lab.sys.platform", "linux")
    @patch("shared.clipboard_lab.os.environ.get")
    @patch("shared.clipboard_lab.shutil.which")
    @patch("shared.clipboard_lab.subprocess.run")
    def test_copy_system_fallback_linux_xclip(self, mock_run, mock_which, mock_env):
        mock_env.return_value = None # No Wayland
        # mock_which side effect to find xclip but not others if needed,
        # but implementation checks wayland first, then xclip.
        def which_side_effect(cmd):
            return "/usr/bin/xclip" if cmd == "xclip" else None
        mock_which.side_effect = which_side_effect

        mock_run.return_value.returncode = 0

        success = self.manager.copy_to_system("linux copy")
        self.assertTrue(success)
        mock_run.assert_called_with(["xclip", "-selection", "clipboard"], input=b"linux copy", check=True)

    @patch("shared.clipboard_lab.HAS_PYPERCLIP", True)
    def test_copy_pyperclip(self):
        mock_pyperclip = MagicMock()
        import shared.clipboard_lab

        original_pyperclip = shared.clipboard_lab.pyperclip
        shared.clipboard_lab.pyperclip = mock_pyperclip

        try:
            success = self.manager.copy_to_system("pyperclip copy")
            self.assertTrue(success)
            mock_pyperclip.copy.assert_called_with("pyperclip copy")

            history = self.manager.get_history()
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0]["text"], "pyperclip copy")
        finally:
            shared.clipboard_lab.pyperclip = original_pyperclip

    def test_history_persistence(self):
        self.manager.add_to_history("item 1")
        self.manager.add_to_history("item 2")

        # Reload
        new_manager = ClipboardManager(self.project_dir)
        history = new_manager.get_history()

        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["text"], "item 2")
        self.assertEqual(history[1]["text"], "item 1")

    def test_clear_history(self):
        self.manager.add_to_history("item")
        self.manager.clear_history()
        self.assertEqual(len(self.manager.get_history()), 0)

if __name__ == "__main__":
    unittest.main()
