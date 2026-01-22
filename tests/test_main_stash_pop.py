
from main import run_stash
import unittest
from unittest.mock import patch, MagicMock
import subprocess
import tempfile
import shutil
from pathlib import Path
import sys
import io

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))


class TestStashCommand(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir) / "test_project"
        self.project_dir.mkdir()

        # Initialize a git repository
        subprocess.run(["git", "init"], cwd=self.project_dir, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.project_dir)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.project_dir)

        # Create an initial commit
        (self.project_dir / "initial_file.txt").write_text("initial content")
        subprocess.run(["git", "add", "."], cwd=self.project_dir, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.project_dir, capture_output=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _create_uncommitted_changes(self):
        (self.project_dir / "new_file.txt").write_text("new file content")
        (self.project_dir / "initial_file.txt").write_text("modified content")

    def test_stash_push_with_changes(self):
        self._create_uncommitted_changes()
        args = MagicMock(action="push", message="test stash", project_dir=self.project_dir)

        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            run_stash(args)
            output = mock_stdout.getvalue()
            self.assertIn("Changes stashed successfully.", output)
            self.assertIn("stash@{0}", output)

        result = subprocess.run(["git", "stash", "list"], cwd=self.project_dir, capture_output=True, text=True)
        self.assertIn("test stash", result.stdout)

    def test_stash_list(self):
        self._create_uncommitted_changes()
        subprocess.run(["git", "stash", "push", "-u", "-m", "first stash"], cwd=self.project_dir, capture_output=True)

        args = MagicMock(action="list", project_dir=self.project_dir)
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            run_stash(args)
            output = mock_stdout.getvalue()
            self.assertIn("stash@{0}: On master: first stash", output)

    @patch('builtins.input', return_value='0')
    def test_stash_pop(self, mock_input):
        self._create_uncommitted_changes()
        subprocess.run(["git", "stash", "push", "-u", "-m", "pop test"], cwd=self.project_dir, capture_output=True)

        args = MagicMock(action="pop", project_dir=self.project_dir)
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            run_stash(args)
            output = mock_stdout.getvalue()
            self.assertIn("Stash stash@{0} popped successfully.", output)

        result = subprocess.run(["git", "stash", "list"], cwd=self.project_dir, capture_output=True, text=True)
        self.assertEqual(result.stdout.strip(), "")

    @patch('builtins.input', side_effect=['0', 'y'])
    def test_stash_drop(self, mock_input):
        self._create_uncommitted_changes()
        subprocess.run(["git", "stash", "push", "-u", "-m", "drop test"], cwd=self.project_dir, capture_output=True)

        args = MagicMock(action="drop", project_dir=self.project_dir, yes=False)
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            run_stash(args)
            output = mock_stdout.getvalue()
            self.assertIn("Stash stash@{0} dropped successfully.", output)

        result = subprocess.run(["git", "stash", "list"], cwd=self.project_dir, capture_output=True, text=True)
        self.assertEqual(result.stdout.strip(), "")


if __name__ == '__main__':
    unittest.main()
