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
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestMainDiscard(unittest.TestCase):
    def setUp(self):
        """Set up a temporary git repository for each test."""
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)

        subprocess.run(["git", "-c", "advice.detachedHead=false", "init"], cwd=self.project_dir, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.project_dir, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.project_dir, check=True)

        self.initial_file = self.project_dir / "initial_file.txt"
        self.initial_file.write_text("initial content")
        subprocess.run(["git", "add", self.initial_file], cwd=self.project_dir, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.project_dir, check=True)

        self.modified_file = self.project_dir / "modified_file.txt"
        self.modified_file.write_text("original content")
        subprocess.run(["git", "add", self.modified_file], cwd=self.project_dir, check=True)
        subprocess.run(["git", "commit", "-m", "Add modified_file"], cwd=self.project_dir, check=True)
        self.modified_file.write_text("modified content")

        self.untracked_file = self.project_dir / "untracked_file.txt"
        self.untracked_file.write_text("untracked content")

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.test_dir)

    def _run_discard(self, args_list):
        """Helper function to run the discard command."""
        argv = ['discard'] + args_list + ['--project-dir', str(self.project_dir)]
        args = main.parse_args(argv)
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout, \
                patch('sys.stderr', new_callable=io.StringIO) as mock_stderr:
            with self.assertRaises(SystemExit) as cm:
                main.run_discard(args)
            return cm.exception.code, mock_stdout.getvalue(), mock_stderr.getvalue()

    def test_discard_all_changes(self):
        """Test discarding all changes with --yes."""
        self.assertEqual((self.project_dir / "modified_file.txt").read_text(), "modified content")
        self.assertTrue((self.project_dir / "untracked_file.txt").exists())

        exit_code, output, stderr = self._run_discard(['--yes'])

        self.assertEqual(exit_code, 0)
        self.assertIn("Discarding ALL uncommitted changes", output)
        self.assertIn("Discard complete", output)

        self.assertEqual((self.project_dir / "modified_file.txt").read_text(), "original content")
        self.assertFalse((self.project_dir / "untracked_file.txt").exists())

    def test_discard_specific_files(self):
        """Test discarding a specific modified and untracked file with --yes."""
        self.assertEqual((self.project_dir / "modified_file.txt").read_text(), "modified content")
        self.assertTrue((self.project_dir / "untracked_file.txt").exists())

        exit_code, output, stderr = self._run_discard(['modified_file.txt', 'untracked_file.txt', '--yes'])

        self.assertEqual(exit_code, 0)
        self.assertIn("Discarding files...", output)
        self.assertIn("✅ Specified files have been discarded.", output)

        self.assertEqual((self.project_dir / "modified_file.txt").read_text(), "original content")
        self.assertFalse((self.project_dir / "untracked_file.txt").exists())

    @patch('builtins.input', side_effect=['1', 'y'])
    def test_discard_interactive_select_modified(self, mock_input):
        """Test discarding a single modified file in interactive mode."""
        self.assertEqual((self.project_dir / "modified_file.txt").read_text(), "modified content")

        exit_code, output, stderr = self._run_discard(['--interactive'])

        self.assertEqual(exit_code, 0)
        self.assertIn("--- Interactive Discard", output)
        self.assertIn("M: modified_file.txt", output)
        self.assertIn("✅ Specified files have been discarded.", output)
        self.assertEqual((self.project_dir / "modified_file.txt").read_text(), "original content")

    @patch('builtins.input', side_effect=['2', 'y'])
    def test_discard_interactive_select_untracked(self, mock_input):
        """Test discarding a single untracked file in interactive mode."""
        self.assertTrue((self.project_dir / "untracked_file.txt").exists())

        exit_code, output, stderr = self._run_discard(['--interactive'])

        self.assertEqual(exit_code, 0)
        self.assertIn("??: untracked_file.txt", output)
        self.assertIn("✅ Specified files have been discarded.", output)
        self.assertFalse((self.project_dir / "untracked_file.txt").exists())

    @patch('builtins.input', side_effect=['1 2', 'y'])
    def test_discard_interactive_select_mixed(self, mock_input):
        """Test discarding both a modified and an untracked file."""
        self.assertEqual((self.project_dir / "modified_file.txt").read_text(), "modified content")
        self.assertTrue((self.project_dir / "untracked_file.txt").exists())

        exit_code, output, stderr = self._run_discard(['--interactive'])

        self.assertEqual(exit_code, 0)
        self.assertIn("✅ Specified files have been discarded.", output)
        self.assertEqual((self.project_dir / "modified_file.txt").read_text(), "original content")
        self.assertFalse((self.project_dir / "untracked_file.txt").exists())

    @patch('builtins.input', return_value='')
    def test_discard_interactive_cancel_with_enter(self, mock_input):
        """Test cancelling the interactive prompt by pressing Enter."""
        exit_code, output, stderr = self._run_discard(['--interactive'])
        self.assertEqual(exit_code, 0)
        self.assertIn("Aborted.", output)
        self.assertEqual((self.project_dir / "modified_file.txt").read_text(), "modified content")
        self.assertTrue((self.project_dir / "untracked_file.txt").exists())

    @patch('builtins.input', return_value='not-a-number')
    def test_discard_interactive_invalid_input(self, mock_input):
        """Test that non-numeric input results in a graceful exit."""
        exit_code, output, stderr = self._run_discard(['--interactive'])
        self.assertEqual(exit_code, 1)
        self.assertIn("Invalid input", stderr)
        self.assertEqual((self.project_dir / "modified_file.txt").read_text(), "modified content")
        self.assertTrue((self.project_dir / "untracked_file.txt").exists())

    def test_discard_interactive_no_changes(self):
        """Test interactive discard when the repository is clean."""
        subprocess.run(["git", "reset", "--hard", "HEAD"], cwd=self.project_dir, check=True)
        subprocess.run(["git", "clean", "-fd"], cwd=self.project_dir, check=True)

        exit_code, output, stderr = self._run_discard(['--interactive'])
        self.assertEqual(exit_code, 0)
        self.assertIn("✅ No uncommitted changes to discard.", output)

    def test_discard_files_and_interactive_fails(self):
        """Test that using --interactive with specified files is not allowed."""
        exit_code, output, stderr = self._run_discard(['--interactive', 'some_file.txt'])
        self.assertEqual(exit_code, 1)
        self.assertIn("Error: Cannot use --interactive mode when specifying individual files.", stderr)


if __name__ == '__main__':
    unittest.main()
