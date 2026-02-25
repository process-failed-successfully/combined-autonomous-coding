import unittest
import shutil
import os
from pathlib import Path
from unittest.mock import MagicMock, patch
from shared.clipboard_lab import ClipboardManager

class TestClipboardManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("test_clipboard_lab")
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir(exist_ok=True)

        self.history_file = self.test_dir / ".clipboard_history.json"

        # Default mock clipboard for basic tests
        self.mock_clipboard = MagicMock()
        # Initialize with mock clipboard, assuming present by default
        self.manager = ClipboardManager(self.test_dir, clipboard_module=self.mock_clipboard, has_clipboard=True)

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

        # New manager instance same dir, verify it loads existing history
        # We don't need mock clipboard for persistence check
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

    @patch.dict(os.environ, {"CI": "", "FORCE_CLIPBOARD": ""})
    def test_system_sync(self):
        self.mock_clipboard.paste.return_value = "system content"

        # Test adding TO system (called inside add)
        self.manager.add("manual content")
        self.mock_clipboard.copy.assert_called_with("manual content")

        # Reset mock to test sync loop prevention
        self.mock_clipboard.copy.reset_mock()

        # Test syncing FROM system
        added = self.manager.sync_system()
        self.assertTrue(added)
        self.assertEqual(self.manager.get(0), "system content")
        self.assertEqual(self.manager.list_history()[0]["source"], "system")

        # Verify sync_system (which calls add with source="system") does NOT call copy back
        self.mock_clipboard.copy.assert_not_called()

        # Sync again (no change)
        added = self.manager.sync_system()
        self.assertFalse(added)

    def test_sync_system_no_pyperclip(self):
        # Create manager with no clipboard
        manager = ClipboardManager(self.test_dir, clipboard_module=None, has_clipboard=False)
        self.assertFalse(manager.sync_system())

    @patch.dict(os.environ, {"CI": "true", "FORCE_CLIPBOARD": ""})
    def test_sync_system_ci_skip(self):
        # Manager has clipboard (default in setUp), but CI should prevent sync
        self.assertFalse(self.manager.sync_system())

    @patch.dict(os.environ, {"CI": "true", "FORCE_CLIPBOARD": "1"})
    def test_sync_system_ci_force(self):
        self.mock_clipboard.paste.return_value = "forced content"
        self.assertTrue(self.manager.sync_system())
        self.assertEqual(self.manager.get(0), "forced content")

    @patch.dict(os.environ, {"CI": "true", "FORCE_CLIPBOARD": ""})
    def test_add_skips_in_ci(self):
        # Ensure fresh history to avoid deduplication skipping copy attempt
        self.manager.clear()
        self.manager.add("test ci skip")
        self.mock_clipboard.copy.assert_not_called()

    @patch.dict(os.environ, {"CI": "true", "FORCE_CLIPBOARD": "1"})
    def test_add_runs_in_ci_force(self):
        self.manager.clear()
        self.manager.add("test ci force")
        self.mock_clipboard.copy.assert_called_with("test ci force")

if __name__ == "__main__":
    unittest.main()
