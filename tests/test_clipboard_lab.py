import unittest
import shutil
from pathlib import Path
from unittest.mock import patch
from shared.clipboard_lab import ClipboardManager


class TestClipboardManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("test_clipboard_lab")
        self.test_dir.mkdir(exist_ok=True)
        self.history_file = self.test_dir / ".clipboard_history.json"
        self.manager = ClipboardManager(self.test_dir)

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_add_and_get(self):
        self.manager.add("test content")
        self.assertEqual(self.manager.get(0), "test content")

        history = self.manager.list_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["content"], "test content")

    def test_persistence(self):
        self.manager.add("persistent content")

        # New manager instance same dir
        new_manager = ClipboardManager(self.test_dir)
        self.assertEqual(new_manager.get(0), "persistent content")

    def test_deduplication(self):
        self.manager.add("dup")
        self.manager.add("dup")
        self.assertEqual(len(self.manager.list_history()), 1)

        self.manager.add("new")
        self.assertEqual(len(self.manager.list_history()), 2)
        self.assertEqual(self.manager.get(0), "new")

    def test_delete_and_update(self):
        self.manager.add("item 2")
        self.manager.add("item 1")  # index 0

        # Test update
        updated = self.manager.update(0, "item 1 updated")
        self.assertTrue(updated)
        self.assertEqual(self.manager.get(0), "item 1 updated")

        # Test delete
        deleted = self.manager.delete(0)
        self.assertTrue(deleted)
        self.assertEqual(self.manager.get(0), "item 2")

        # Test invalid index
        self.assertFalse(self.manager.delete(99))
        self.assertFalse(self.manager.update(99, "bad"))

    def test_clear(self):
        self.manager.add("to be deleted")
        self.manager.clear()
        self.assertEqual(len(self.manager.list_history()), 0)
        self.assertFalse(self.history_file.exists())

    @patch("shared.clipboard_lab.pyperclip")
    @patch("shared.clipboard_lab.HAS_PYPERCLIP", True)
    def test_system_sync(self, mock_pyperclip):
        mock_pyperclip.paste.return_value = "system content"

        # Test adding TO system (called inside add)
        self.manager.add("manual content")
        mock_pyperclip.copy.assert_called_with("manual content")

        # Test syncing FROM system
        added = self.manager.sync_system()
        self.assertTrue(added)
        self.assertEqual(self.manager.get(0), "system content")
        self.assertEqual(self.manager.list_history()[0]["source"], "system")

        # Sync again (no change)
        added = self.manager.sync_system()
        self.assertFalse(added)


if __name__ == "__main__":
    unittest.main()
