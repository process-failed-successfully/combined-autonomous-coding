import main
import unittest
from unittest.mock import patch
import subprocess
import tempfile
import shutil
from pathlib import Path
import sys
import io

# Add the root of the project to the Python path
# This is necessary for the test runner to find the 'main' module
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestMainRevert(unittest.TestCase):
    def setUp(self):
        """Set up a temporary git repository for each test."""
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)

        # Initialize a git repository
        # Suppress git hints
        subprocess.run(["git", "-c", "advice.detachedHead=false", "init"], cwd=self.project_dir, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.project_dir, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.project_dir, check=True)

        # Create and commit an initial file
        self.initial_file = self.project_dir / "initial_file.txt"
        self.initial_file.write_text("initial content")
        subprocess.run(["git", "add", self.initial_file], cwd=self.project_dir, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.project_dir, check=True)

        # Create a modified file and commit it
        self.modified_file = self.project_dir / "modified_file.txt"
        self.modified_file.write_text("original content")
        subprocess.run(["git", "add", self.modified_file], cwd=self.project_dir, check=True)
        subprocess.run(["git", "commit", "-m", "Add modified_file"], cwd=self.project_dir, check=True)
        # Now modify it
        self.modified_file.write_text("modified content")

        # Create an untracked file
        self.untracked_file = self.project_dir / "untracked_file.txt"
        self.untracked_file.write_text("untracked content")

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.test_dir)

    def _run_revert(self, args_list):
        """Helper function to run the revert command with patched stdin, stdout, and stderr."""
        # Use a copy of argv to avoid conflicts between tests
        argv = ['revert'] + args_list + ['--project-dir', str(self.project_dir)]
        args = main.parse_args(argv)
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout, \
                patch('sys.stderr', new_callable=io.StringIO) as mock_stderr:
            with self.assertRaises(SystemExit) as cm:
                main.run_revert(args)
            return cm.exception.code, mock_stdout.getvalue(), mock_stderr.getvalue()

    # --- Tests for Non-Interactive Mode ---
    def test_revert_all_changes(self):
        """Test reverting all changes with --yes."""
        self.assertEqual((self.project_dir / "modified_file.txt").read_text(), "modified content")
        self.assertTrue((self.project_dir / "untracked_file.txt").exists())

        exit_code, output, stderr = self._run_revert(['--yes'])

        self.assertEqual(exit_code, 0)
        self.assertIn("Reverting ALL uncommitted changes", output)
        self.assertIn("Revert complete", output)

        self.assertEqual((self.project_dir / "modified_file.txt").read_text(), "original content")
        self.assertFalse((self.project_dir / "untracked_file.txt").exists())

    def test_revert_specific_files(self):
        """Test reverting a specific modified and untracked file with --yes."""
        self.assertEqual((self.project_dir / "modified_file.txt").read_text(), "modified content")
        self.assertTrue((self.project_dir / "untracked_file.txt").exists())

        exit_code, output, stderr = self._run_revert(['modified_file.txt', 'untracked_file.txt', '--yes'])

        self.assertEqual(exit_code, 0)
        self.assertIn("Reverting specified files", output)
        self.assertIn("✅ Specified files have been reverted.", output)

        self.assertEqual((self.project_dir / "modified_file.txt").read_text(), "original content")
        self.assertFalse((self.project_dir / "untracked_file.txt").exists())

    # --- Tests for Interactive Mode ---

    @patch('builtins.input', side_effect=['1', 'y'])
    def test_revert_interactive_select_modified(self, mock_input):
        """Test reverting a single modified file in interactive mode."""
        self.assertTrue((self.project_dir / "modified_file.txt").exists())
        self.assertEqual((self.project_dir / "modified_file.txt").read_text(), "modified content")

        exit_code, output, stderr = self._run_revert(['--interactive'])

        self.assertEqual(exit_code, 0)
        self.assertIn("--- Interactive Revert", output)
        self.assertIn("M: modified_file.txt", output)
        self.assertIn("✅ Specified files have been reverted.", output)
        self.assertEqual((self.project_dir / "modified_file.txt").read_text(), "original content")

    @patch('builtins.input', side_effect=['2', 'y'])
    def test_revert_interactive_select_untracked(self, mock_input):
        """Test reverting a single untracked file in interactive mode."""
        self.assertTrue((self.project_dir / "untracked_file.txt").exists())

        exit_code, output, stderr = self._run_revert(['--interactive'])

        self.assertEqual(exit_code, 0)
        self.assertIn("??: untracked_file.txt", output)
        self.assertIn("✅ Specified files have been reverted.", output)
        self.assertFalse((self.project_dir / "untracked_file.txt").exists())

    @patch('builtins.input', side_effect=['1 2', 'y'])
    def test_revert_interactive_select_mixed(self, mock_input):
        """Test reverting both a modified and an untracked file."""
        self.assertEqual((self.project_dir / "modified_file.txt").read_text(), "modified content")
        self.assertTrue((self.project_dir / "untracked_file.txt").exists())

        exit_code, output, stderr = self._run_revert(['--interactive'])

        self.assertEqual(exit_code, 0)
        self.assertIn("✅ Specified files have been reverted.", output)
        self.assertEqual((self.project_dir / "modified_file.txt").read_text(), "original content")
        self.assertFalse((self.project_dir / "untracked_file.txt").exists())

    @patch('builtins.input', return_value='')
    def test_revert_interactive_cancel_with_enter(self, mock_input):
        """Test cancelling the interactive prompt by pressing Enter."""
        exit_code, output, stderr = self._run_revert(['--interactive'])
        self.assertEqual(exit_code, 0)
        self.assertIn("Aborted.", output)
        # Assert files are unchanged
        self.assertEqual((self.project_dir / "modified_file.txt").read_text(), "modified content")
        self.assertTrue((self.project_dir / "untracked_file.txt").exists())

    @patch('builtins.input', return_value='not-a-number')
    def test_revert_interactive_invalid_input(self, mock_input):
        """Test that non-numeric input results in a graceful exit."""
        exit_code, output, stderr = self._run_revert(['--interactive'])
        self.assertEqual(exit_code, 1)
        self.assertIn("Invalid input", stderr)
        # Assert files are unchanged
        self.assertEqual((self.project_dir / "modified_file.txt").read_text(), "modified content")
        self.assertTrue((self.project_dir / "untracked_file.txt").exists())

    def test_revert_interactive_no_changes(self):
        """Test interactive revert when the repository is clean."""
        # Clean the repo first
        subprocess.run(["git", "reset", "--hard", "HEAD"], cwd=self.project_dir, check=True)
        subprocess.run(["git", "clean", "-fd"], cwd=self.project_dir, check=True)

        exit_code, output, stderr = self._run_revert(['--interactive'])
        self.assertEqual(exit_code, 0)
        self.assertIn("✅ No uncommitted changes to revert.", output)

    def test_revert_files_and_interactive_fails(self):
        """Test that using --interactive with specified files is not allowed."""
        exit_code, output, stderr = self._run_revert(['--interactive', 'some_file.txt'])
        self.assertEqual(exit_code, 1)
        self.assertIn("Error: Cannot use --interactive mode when specifying individual files.", stderr)


if __name__ == '__main__':
    unittest.main()
