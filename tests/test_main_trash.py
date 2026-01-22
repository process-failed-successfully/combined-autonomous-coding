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
        self.file_name = "file1.txt"
        self.trashed_file = self.archive_dir / self.file_name

        (self.trashed_file).write_text("This is file one.\n")
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
            yes=True,  # Default to yes to avoid interactive prompts
            all='--all' in (extra_args or []),
            dry_run='--dry-run' in (extra_args or [])
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

    @patch('builtins.input', side_effect=['1'])  # Simulate user selecting the first (latest) archive
    def test_trash_restore_latest_interactive(self, mock_input):
        """Test restoring the latest archive interactively when no name is specified."""
        # Create a newer archive
        newer_archive_name = "trash-2023-01-02_12-00-00"
        newer_archive_dir = self.trash_base_dir / newer_archive_name
        newer_archive_dir.mkdir()
        (newer_archive_dir / "latest_file.txt").write_text("This is from the latest archive.")

        # run_trash_command is not used here due to the need for a custom mock setup
        mock_args = argparse.Namespace(
            command='trash',
            action='restore',
            archive_name=None,
            file_name=None,
            project_dir=self.project_dir,
            yes=True,
            all=False,
            dry_run=False
        )

        f = io.StringIO()
        with redirect_stdout(f), patch('main.parse_args', return_value=mock_args):
            with self.assertRaises(SystemExit) as cm:
                main_script.run_trash(mock_args)
            self.assertEqual(cm.exception.code, 0)

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

    def test_restore_dry_run(self):
        """Verify that 'trash restore --dry-run' shows actions without restoring."""
        output = self.run_trash_command('restore', self.archive_name, extra_args=['--dry-run'])

        # Check that the output indicates a dry run
        self.assertIn("-- DRY RUN --", output)
        self.assertIn("The following actions would be taken:", output)
        self.assertIn(f"MOVE: {self.file_name} from trash to project directory", output)
        self.assertIn(f"DELETE: Empty archive '{self.archive_name}'", output)
        self.assertIn("No changes were made.", output)

        # Verify that no changes were actually made
        self.assertTrue(self.trashed_file.exists())
        self.assertFalse((self.project_dir / self.file_name).exists())

    def test_clear_archive_dry_run(self):
        """Verify that 'trash clear <archive> --dry-run' shows actions without deleting."""
        output = self.run_trash_command('clear', self.archive_name, extra_args=['--dry-run'])

        self.assertIn("-- DRY RUN --", output)
        self.assertIn(f"Would permanently delete the archive: {self.archive_name}", output)
        self.assertIn("No changes were made.", output)

        # Verify that the archive still exists
        self.assertTrue(self.archive_dir.exists())

    def test_clear_all_dry_run(self):
        """Verify that 'trash clear --all --dry-run' shows actions without deleting."""
        # Create a second archive to ensure it would clear all
        (self.trash_base_dir / "trash-2023-01-02_12-00-00").mkdir()

        output = self.run_trash_command('clear', extra_args=['--all', '--dry-run'])

        self.assertIn("-- DRY RUN --", output)
        self.assertIn("Would permanently delete the entire '.agent_trash' directory", output)
        self.assertIn("No changes were made.", output)

        # Verify that the trash directory and its contents still exist
        self.assertTrue(self.trash_base_dir.exists())
        self.assertEqual(len(list(self.trash_base_dir.iterdir())), 2)


if __name__ == '__main__':
    unittest.main()
