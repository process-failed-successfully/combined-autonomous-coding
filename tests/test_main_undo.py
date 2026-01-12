import unittest
from unittest.mock import patch, MagicMock
from io import StringIO
import subprocess
import tempfile
import shutil
from pathlib import Path
import os
import sys
import re

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from main import run_undo

class TestMainUndo(unittest.TestCase):
    def strip_ansi_codes(self, text):
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        self.git_path = shutil.which("git")

        # Basic git setup
        subprocess.run([self.git_path, "init", "-b", "main"], cwd=self.project_dir, check=True)
        subprocess.run([self.git_path, "config", "user.name", "Test User"], cwd=self.project_dir, check=True)
        subprocess.run([self.git_path, "config", "user.email", "test@example.com"], cwd=self.project_dir, check=True)

        # Create and commit a file
        (self.project_dir / "file1.txt").write_text("initial content")
        subprocess.run([self.git_path, "add", "file1.txt"], cwd=self.project_dir, check=True)
        subprocess.run([self.git_path, "commit", "-m", "Initial commit"], cwd=self.project_dir, check=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _create_discard_stash(self, filename, content, message):
        """Helper to create a file, modify it, and stash the changes."""
        (self.project_dir / filename).write_text(content)
        subprocess.run([self.git_path, "add", filename], cwd=self.project_dir, check=True)
        (self.project_dir / filename).write_text(content + "\nmore changes")
        subprocess.run(
            [self.git_path, "stash", "push", "-u", "-m", message],
            cwd=self.project_dir,
            check=True
        )
        # Reset the repo to a clean state after stashing
        subprocess.run([self.git_path, "reset", "--hard", "HEAD"], cwd=self.project_dir, check=True)


    @patch('sys.stdout', new_callable=StringIO)
    def test_undo_no_stashes(self, mock_stdout):
        args = MagicMock(project_dir=self.project_dir)
        with self.assertRaises(SystemExit) as cm:
            run_undo(args)
        self.assertEqual(cm.exception.code, 0)
        self.assertIn("No stashed discards found to undo.", mock_stdout.getvalue())

    @patch('builtins.input', side_effect=['q'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_undo_list_and_quit(self, mock_stdout, mock_input):
        self._create_discard_stash("file2.txt", "content2", "agent-discard-stash-1")
        self._create_discard_stash("file3.txt", "content3", "agent-discard-stash-2")

        args = MagicMock(project_dir=self.project_dir)
        with self.assertRaises(SystemExit) as cm:
            run_undo(args)

        self.assertEqual(cm.exception.code, 0)
        output = mock_stdout.getvalue()
        self.assertIn("Available discards:", output)
        self.assertIn("agent-discard-stash-1", output)
        self.assertIn("agent-discard-stash-2", output)
        self.assertIn("file2.txt", output)
        self.assertIn("file3.txt", output)
        self.assertIn("Aborted.", output)

    @patch('builtins.input', side_effect=['d 1', '', 'q'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_undo_show_diff(self, mock_stdout, mock_input):
        self._create_discard_stash("diff_file.txt", "diff content", "agent-discard-stash-diff")

        args = MagicMock(project_dir=self.project_dir)
        with self.assertRaises(SystemExit) as cm:
            run_undo(args)

        self.assertEqual(cm.exception.code, 0)
        output = self.strip_ansi_codes(mock_stdout.getvalue())
        self.assertIn("--- Diff for stash@{0} ---", output)
        # Check that the diff content is present
        self.assertIn("diff --git a/diff_file.txt b/diff_file.txt", output)
        self.assertIn("+++ b/diff_file.txt", output)
        self.assertIn("+more changes", output)

    @patch('builtins.input', side_effect=['1'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_undo_restore(self, mock_stdout, mock_input):
        self._create_discard_stash("restore_me.txt", "restore content", "agent-discard-stash-restore")
        self.assertFalse((self.project_dir / "restore_me.txt").exists())

        args = MagicMock(project_dir=self.project_dir)
        with self.assertRaises(SystemExit) as cm:
            run_undo(args)

        self.assertEqual(cm.exception.code, 0)
        output = mock_stdout.getvalue()
        self.assertIn("Restoring selected stash: stash@{0}", output)
        self.assertIn("Undo complete. Your changes have been restored.", output)

        # Verify the file is restored
        self.assertTrue((self.project_dir / "restore_me.txt").exists())
        content = (self.project_dir / "restore_me.txt").read_text()
        self.assertEqual(content, "restore content\nmore changes")

    @patch('builtins.input', side_effect=['99', 'invalid', 'q'])
    @patch('sys.stderr', new_callable=StringIO)
    @patch('sys.stdout', new_callable=StringIO)
    def test_undo_invalid_selections(self, mock_stdout, mock_stderr, mock_input):
        self._create_discard_stash("file.txt", "content", "agent-discard-stash-invalid")

        args = MagicMock(project_dir=self.project_dir)
        with self.assertRaises(SystemExit) as cm:
            run_undo(args)

        self.assertEqual(cm.exception.code, 0)
        stderr_output = mock_stderr.getvalue()
        self.assertIn("Invalid selection.", stderr_output)
        self.assertIn("Invalid input. Please enter a number", stderr_output)
        self.assertIn("Aborted.", mock_stdout.getvalue())

if __name__ == '__main__':
    unittest.main()
