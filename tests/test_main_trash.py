import unittest
from unittest.mock import patch, MagicMock
import argparse
from pathlib import Path
import shutil
import io
import sys
from datetime import datetime

# Make sure the main module can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from main import run_trash

class TestMainTrash(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory and trash structure for testing."""
        self.test_dir = Path("./test_trash_temp")
        self.test_dir.mkdir(exist_ok=True)
        self.trash_dir = self.test_dir / ".agent_trash"
        self.trash_dir.mkdir(exist_ok=True)

        # Create some dummy archives and files
        self.archive1_name = "trash-2023-01-01_12-00-00"
        self.archive2_name = "trash-2023-01-02_12-00-00"
        self.archive1_path = self.trash_dir / self.archive1_name
        self.archive2_path = self.trash_dir / self.archive2_name
        self.archive1_path.mkdir()
        self.archive2_path.mkdir()

        (self.archive1_path / "file1.txt").write_text("file1 content")
        (self.archive2_path / "file2.txt").write_text("file2 content")
        (self.archive2_path / "subdir").mkdir()
        (self.archive2_path / "subdir" / "file3.txt").write_text("file3 content")

        # Redirect stdout to capture print statements
        self.held_stdout = sys.stdout
        sys.stdout = io.StringIO()

    def tearDown(self):
        """Clean up the temporary directory."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        # Restore stdout
        sys.stdout = self.held_stdout

    def test_trash_list_empty(self):
        # Arrange
        shutil.rmtree(self.trash_dir)
        self.trash_dir.mkdir()
        args = argparse.Namespace(
            command="trash",
            action="list",
            project_dir=self.test_dir,
        )

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_trash(args)

        # Assert
        self.assertEqual(cm.exception.code, 0)
        output = sys.stdout.getvalue()
        self.assertIn("Trash is empty.", output)

    def test_trash_clear_specific_archive(self):
        # Arrange
        args = argparse.Namespace(
            command="trash",
            action="clear",
            archive_name=self.archive1_name,
            project_dir=self.test_dir,
            all=False,
            yes=True,
        )

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_trash(args)

        # Assert
        self.assertEqual(cm.exception.code, 0)
        self.assertFalse(self.archive1_path.exists())
        self.assertTrue(self.archive2_path.exists())
        output = sys.stdout.getvalue()
        self.assertIn(f"Archive '{self.archive1_name}' deleted.", output)

    def test_trash_clear_all_archives(self):
        # Arrange
        args = argparse.Namespace(
            command="trash",
            action="clear",
            archive_name=None,
            project_dir=self.test_dir,
            all=True,
            yes=True,
        )

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_trash(args)

        # Assert
        self.assertEqual(cm.exception.code, 0)
        self.assertFalse(self.trash_dir.exists())
        output = sys.stdout.getvalue()
        self.assertIn("Trash successfully emptied.", output)

    def test_trash_restore_latest(self):
        # Arrange
        args = argparse.Namespace(
            command="trash",
            action="restore",
            archive_name=None, # Restore the latest
            project_dir=self.test_dir,
            yes=True,
        )

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_trash(args)

        # Assert
        self.assertEqual(cm.exception.code, 0)
        self.assertTrue((self.test_dir / "file2.txt").exists())
        self.assertTrue((self.test_dir / "subdir" / "file3.txt").exists())
        self.assertFalse(self.archive2_path.exists()) # Should be removed after restore
        output = sys.stdout.getvalue()
        self.assertIn("Restore complete.", output)

    def test_trash_restore_specific_archive(self):
        # Arrange
        args = argparse.Namespace(
            command="trash",
            action="restore",
            archive_name=self.archive1_name,
            project_dir=self.test_dir,
            yes=True,
        )

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_trash(args)

        # Assert
        self.assertEqual(cm.exception.code, 0)
        self.assertTrue((self.test_dir / "file1.txt").exists())
        self.assertFalse(self.archive1_path.exists())
        output = sys.stdout.getvalue()
        self.assertIn("Restore complete.", output)

    def test_trash_restore_conflict(self):
        # Arrange
        (self.test_dir / "file1.txt").write_text("existing file")
        args = argparse.Namespace(
            command="trash",
            action="restore",
            archive_name=self.archive1_name,
            project_dir=self.test_dir,
            yes=True,
        )

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_trash(args)

        # Assert
        self.assertEqual(cm.exception.code, 1)
        output = sys.stdout.getvalue()
        self.assertIn("The following files already exist", output)
        self.assertIn("file1.txt", output)
        self.assertTrue(self.archive1_path.exists()) # Should not be deleted

    def test_trash_list_with_log_summary(self):
        """Test that `trash list` shows a log summary if a log file is present."""
        # Arrange
        log_content = "\n".join([f"Line {i}" for i in range(20)])
        (self.archive2_path / "test_run_123.log").write_text(log_content)

        args = argparse.Namespace(
            command="trash",
            action="list",
            project_dir=self.test_dir,
        )

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_trash(args)

        # Assert
        self.assertEqual(cm.exception.code, 0)
        output = sys.stdout.getvalue()

        self.assertIn(self.archive2_name, output)
        # Check that other files are still listed
        self.assertIn("file2.txt", output)
        self.assertIn("subdir/ (dir)", output)
        self.assertIn("test_run_123.log", output)

        # Check for log summary details
        self.assertIn("--- Log Summary (last 15 lines) ---", output)
        self.assertIn("Line 5", output)
        self.assertIn("Line 19", output)
        self.assertNotIn("Line 4", output)

if __name__ == '__main__':
    unittest.main()
