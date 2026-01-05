import unittest
from unittest.mock import patch
import argparse
from pathlib import Path
import shutil
import tempfile
import io
from contextlib import redirect_stdout

import main as main_script

class TestMainTrashCommand(unittest.TestCase):
    def setUp(self):
        """Set up a temporary directory with a simulated project and trash."""
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        self.trash_base_dir = self.project_dir / ".agent_trash"
        self.trash_base_dir.mkdir()

        # Create a sample trash archive
        self.archive_name = "trash-2023-01-01_12-00-00"
        self.archive_dir = self.trash_base_dir / self.archive_name
        self.archive_dir.mkdir()

        (self.archive_dir / "file1.txt").write_text("This is file one.\n")
        (self.archive_dir / "file2.log").write_text("Log line 1\nLog line 2\n" * 10)

    def tearDown(self):
        """Remove the temporary directory."""
        shutil.rmtree(self.test_dir)

    def run_trash_command(self, action, archive_name=None, file_name=None, extra_args=None):
        """Helper to run the trash command and capture its output."""
        args_list = ['trash', action]
        if archive_name:
            args_list.append(archive_name)
        if file_name:
            args_list.append(file_name)
        if extra_args:
            args_list.extend(extra_args)

        # Mocking argparse Namespace
        mock_args = argparse.Namespace(
            command='trash',
            action=action,
            archive_name=archive_name,
            file_name=file_name,
            project_dir=self.project_dir,
            yes=True, # Default to yes to avoid interactive prompts
            all='--all' in (extra_args or [])
        )

        f = io.StringIO()
        with redirect_stdout(f), patch('main.parse_args', return_value=mock_args):
            try:
                main_script.run_trash(mock_args)
            except SystemExit as e:
                # We expect sys.exit(0) on success
                self.assertEqual(e.code, 0, "Command should exit with 0 on success")
        return f.getvalue()

    def test_setup_is_correct(self):
        """Verify that the test setup and file structure are correct."""
        self.assertTrue(self.archive_dir.exists())
        self.assertTrue((self.archive_dir / "file1.txt").exists())

    def test_trash_inspect_archive_summary(self):
        """Test the 'inspect' action for an archive summary."""
        output = self.run_trash_command('inspect', self.archive_name)
        self.assertIn(f"--- Inspecting Archive: {self.archive_name} ---", output)
        self.assertIn("--- File: file1.txt ---", output)
        self.assertIn("This is file one.", output)
        self.assertIn("--- File: file2.log ---", output)
        self.assertIn("Log line 1", output)
        self.assertIn("...", output, "Should show ellipsis for truncated file")

    def test_trash_inspect_specific_file(self):
        """Test the 'inspect' action for a specific file."""
        output = self.run_trash_command('inspect', self.archive_name, 'file1.txt')
        self.assertIn(f"--- Contents of file1.txt from {self.archive_name} ---", output)
        self.assertIn("This is file one.", output)
        self.assertNotIn("Log line 1", output)

    def test_trash_inspect_specific_long_file(self):
        """Test inspecting a file longer than the preview."""
        full_content = "Log line 1\nLog line 2\n" * 10
        output = self.run_trash_command('inspect', self.archive_name, 'file2.log')
        self.assertIn(full_content, output)
        self.assertNotIn("...", output)

    def test_trash_list(self):
        """Test the 'list' action."""
        output = self.run_trash_command('list')
        self.assertIn(self.archive_name, output)
        self.assertIn("- file1.txt", output)
        self.assertIn("- file2.log", output)

    def test_trash_restore(self):
        """Test the 'restore' action."""
        self.assertFalse((self.project_dir / "file1.txt").exists())
        self.run_trash_command('restore', self.archive_name)
        self.assertTrue((self.project_dir / "file1.txt").exists())
        self.assertTrue((self.project_dir / "file2.log").exists())
        self.assertFalse(self.archive_dir.exists())

    def test_trash_clear_specific_archive(self):
        """Test the 'clear' action on a specific archive."""
        self.assertTrue(self.archive_dir.exists())
        self.run_trash_command('clear', self.archive_name)
        self.assertFalse(self.archive_dir.exists())

    def test_trash_clear_all(self):
        """Test the 'clear' action with the --all flag."""
        # Create another archive to ensure it's also deleted
        (self.trash_base_dir / "another_archive").mkdir()
        self.assertTrue(self.archive_dir.exists())
        self.run_trash_command('clear', extra_args=['--all'])
        self.assertFalse(self.trash_base_dir.exists())

    def test_trash_restore_latest(self):
        """Test restoring the latest archive when no name is specified."""
        # Create a newer archive
        newer_archive_name = "trash-2023-01-02_12-00-00"
        newer_archive_dir = self.trash_base_dir / newer_archive_name
        newer_archive_dir.mkdir()
        (newer_archive_dir / "latest_file.txt").write_text("This is from the latest archive.")

        self.run_trash_command('restore') # No archive name provided
        self.assertTrue((self.project_dir / "latest_file.txt").exists())
        self.assertFalse((self.project_dir / "file1.txt").exists())
        self.assertFalse(newer_archive_dir.exists())

    def test_trash_restore_conflict(self):
        """Test that restore fails if a file conflict is detected."""
        (self.project_dir / "file1.txt").write_text("Existing file.")

        # Use a custom helper to check for non-zero exit code
        with self.assertRaises(AssertionError):
            self.run_trash_command('restore', self.archive_name)

    def test_trash_list_empty(self):
        """Test listing an empty trash directory."""
        shutil.rmtree(self.trash_base_dir)
        self.trash_base_dir.mkdir()
        output = self.run_trash_command('list')
        self.assertIn("Trash is empty.", output)

    def test_trash_list_log_summary(self):
        """Test that 'list' shows a log summary."""
        # Isolate the test by removing the other log file created in setUp
        (self.archive_dir / "file2.log").unlink()

        log_content = "\n".join([f"Line {i}" for i in range(20)])
        (self.archive_dir / "run-123.log").write_text(log_content)
        output = self.run_trash_command('list')
        self.assertIn("--- Log Summary (last 15 lines) ---", output)
        self.assertIn("Line 19", output)
        self.assertNotIn("Line 4", output)


if __name__ == '__main__':
    unittest.main()
