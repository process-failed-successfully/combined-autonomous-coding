import unittest
from unittest.mock import patch
from pathlib import Path
import shutil
import os
import sys
import io

# Ensure the main script can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import main

class TestMainArtifacts(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        """Set up a temporary directory for each test."""
        self.test_dir = Path("test_project_dir")
        self.test_dir.mkdir()

        # Create trash and archives directories
        self.trash_dir = self.test_dir / ".agent_trash"
        self.trash_dir.mkdir()
        self.archive_dir = self.test_dir / ".agent_archives"
        self.archive_dir.mkdir()

        # Create dummy archive contents
        self.trash_archive1 = self.trash_dir / "trash-2023-01-01_12-00-00"
        self.trash_archive1.mkdir()
        (self.trash_archive1 / "file1.txt").write_text("trash file 1")
        (self.trash_archive1 / "file2.log").write_text("log\n" * 20)  # For log summary test

        self.archive_archive1 = self.archive_dir / "archive-2023-01-01_12-00-00"
        self.archive_archive1.mkdir()
        (self.archive_archive1 / "file1.txt").write_text("archive file 1")

    def tearDown(self):
        """Clean up the temporary directory after each test."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    @patch('sys.stdout', new_callable=io.StringIO)
    async def test_artifacts_list_trash_and_archive(self, mock_stdout):
        """Test 'artifacts trash list' and 'artifacts archive list' command."""
        # --- Test Trash List ---
        with self.assertRaises(SystemExit) as cm:
            sys.argv = ["main.py", "artifacts", "trash", "list", "-p", str(self.test_dir)]
            await main()
        self.assertEqual(cm.exception.code, 0)

        output = mock_stdout.getvalue()
        self.assertIn("--- Trash in:", output)
        self.assertIn(self.trash_archive1.name, output)
        self.assertIn("file1.txt", output)
        self.assertIn("file2.log", output)
        self.assertIn("Log Summary", output)  # Check for log summary feature

        # --- Test Archive List ---
        mock_stdout.truncate(0)
        mock_stdout.seek(0)

        with self.assertRaises(SystemExit) as cm:
            sys.argv = ["main.py", "artifacts", "archive", "list", "-p", str(self.test_dir)]
            await main()
        self.assertEqual(cm.exception.code, 0)

        output = mock_stdout.getvalue()
        self.assertIn("--- Archives in:", output)
        self.assertIn(self.archive_archive1.name, output)
        self.assertIn("file1.txt", output)

    @patch('builtins.input', return_value='y')
    async def test_artifacts_restore_trash(self, mock_input):
        """Test 'artifacts trash restore' command."""
        # Restore the trash archive
        with self.assertRaises(SystemExit) as cm:
            sys.argv = ["main.py", "artifacts", "trash", "restore", self.trash_archive1.name, "-p", str(self.test_dir)]
            await main()
        self.assertEqual(cm.exception.code, 0)

        # Check that the files were moved to the project directory
        self.assertTrue((self.test_dir / "file1.txt").exists())
        self.assertEqual((self.test_dir / "file1.txt").read_text(), "trash file 1")

        # Check that the original trash archive is gone
        self.assertFalse(self.trash_archive1.exists())

    @patch('builtins.input', return_value='y')
    async def test_artifacts_restore_archive(self, mock_input):
        """Test 'artifacts archive restore' command."""
        with self.assertRaises(SystemExit) as cm:
            sys.argv = ["main.py", "artifacts", "archive", "restore", self.archive_archive1.name, "-p", str(self.test_dir)]
            await main()
        self.assertEqual(cm.exception.code, 0)

        # Check that the file was copied to the project directory
        self.assertTrue((self.test_dir / "file1.txt").exists())
        self.assertEqual((self.test_dir / "file1.txt").read_text(), "archive file 1")

        # Check that the original archive still exists
        self.assertTrue(self.archive_archive1.exists())

    @patch('sys.stderr', new_callable=io.StringIO)
    async def test_artifacts_restore_conflict(self, mock_stderr):
        """Test that restore fails if a file already exists."""
        # Create a conflicting file in the project directory
        (self.test_dir / "file1.txt").write_text("existing file")

        with self.assertRaises(SystemExit) as cm:
            sys.argv = ["main.py", "artifacts", "trash", "restore", self.trash_archive1.name, "-p", str(self.test_dir)]
            await main()
        self.assertEqual(cm.exception.code, 1)

        output = mock_stderr.getvalue()
        self.assertIn("Error: The following files already exist", output)
        self.assertIn("file1.txt", output)

    @patch('builtins.input', return_value='y')
    async def test_artifacts_clear(self, mock_input):
        """Test the 'clear' action for both trash and archives."""
        # --- Test clearing a specific trash archive ---
        self.assertTrue(self.trash_archive1.exists())
        with self.assertRaises(SystemExit) as cm:
            sys.argv = ["main.py", "artifacts", "trash", "clear", self.trash_archive1.name, "-p", str(self.test_dir)]
            await main()
        self.assertEqual(cm.exception.code, 0)
        self.assertFalse(self.trash_archive1.exists())

        # --- Test clearing all archives ---
        self.assertTrue(self.archive_archive1.exists())
        with self.assertRaises(SystemExit) as cm:
            sys.argv = ["main.py", "artifacts", "archive", "clear", "--all", "-p", str(self.test_dir)]
            await main()
        self.assertEqual(cm.exception.code, 0)
        self.assertFalse(self.archive_dir.exists())

    @patch('sys.stdout', new_callable=io.StringIO)
    async def test_artifacts_inspect_and_diff(self, mock_stdout):
        """Test the 'inspect' and 'diff' actions."""
        # --- Test inspect ---
        with self.assertRaises(SystemExit) as cm:
            sys.argv = ["main.py", "artifacts", "trash", "inspect", self.trash_archive1.name, "file1.txt", "-p", str(self.test_dir)]
            await main()
        self.assertEqual(cm.exception.code, 0)
        self.assertIn("trash file 1", mock_stdout.getvalue())

        # --- Test diff (with changes) ---
        (self.test_dir / "file1.txt").write_text("project file 1")
        mock_stdout.truncate(0)
        mock_stdout.seek(0)

        with self.assertRaises(SystemExit) as cm:
            sys.argv = ["main.py", "artifacts", "trash", "diff", self.trash_archive1.name, "file1.txt", "-p", str(self.test_dir)]
            await main()
        self.assertEqual(cm.exception.code, 0)
        output = mock_stdout.getvalue()
        self.assertIn("--- a/file1.txt", output)
        self.assertIn("+++ b/file1.txt", output)
        self.assertIn("-project file 1", output)
        self.assertIn("+trash file 1", output)

        # --- Test diff (no changes) ---
        (self.test_dir / "file1.txt").write_text("trash file 1")
        mock_stdout.truncate(0)
        mock_stdout.seek(0)

        with self.assertRaises(SystemExit) as cm:
            sys.argv = ["main.py", "artifacts", "trash", "diff", self.trash_archive1.name, "file1.txt", "-p", str(self.test_dir)]
            await main()
        self.assertEqual(cm.exception.code, 0)
        self.assertIn("No differences found", mock_stdout.getvalue())
