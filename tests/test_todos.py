import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.todos import scan_todos, get_todo_blame

class TestTodos(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.project_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        import shutil
        if self.project_dir.exists():
            shutil.rmtree(self.project_dir)

    @patch("shared.todos.subprocess.run")
    @patch("shared.todos.shutil.which")
    def test_scan_todos_git_grep(self, mock_which, mock_run):
        # Setup git environment
        mock_which.return_value = "/usr/bin/git"
        (self.project_dir / ".git").mkdir()

        # Mock git grep output
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "file1.py:10: # TODO: Fix this\nfile2.js:5: // FIXME: Bad code"
        mock_run.return_value = mock_process

        results = scan_todos(self.project_dir, use_git_grep=True)

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['file'], "file1.py")
        self.assertEqual(results[0]['line'], 10)
        self.assertEqual(results[0]['tag'], "TODO")
        self.assertEqual(results[0]['text'], "Fix this")

        self.assertEqual(results[1]['tag'], "FIXME")
        self.assertEqual(results[1]['text'], "Bad code")

    @patch("shared.todos.subprocess.run")
    @patch("shared.todos.shutil.which")
    def test_scan_todos_python_fallback(self, mock_which, mock_run):
        # Simulate no git
        mock_which.return_value = None

        # Create a file
        file_path = self.project_dir / "test.py"
        file_path.write_text("# TODO: Verify fallback\nprint('hello')\n# HACK: Fast fix")

        results = scan_todos(self.project_dir, use_git_grep=False)

        self.assertEqual(len(results), 2)
        # Sort by line to be sure
        results.sort(key=lambda x: x['line'])

        self.assertEqual(results[0]['file'], "test.py")
        self.assertEqual(results[0]['line'], 1)
        self.assertEqual(results[0]['tag'], "TODO")
        self.assertEqual(results[0]['text'], "Verify fallback")

        self.assertEqual(results[1]['line'], 3)
        self.assertEqual(results[1]['tag'], "HACK")
        self.assertEqual(results[1]['text'], "Fast fix")

    @patch("shared.todos.subprocess.run")
    @patch("shared.todos.shutil.which")
    def test_get_todo_blame(self, mock_which, mock_run):
        mock_which.return_value = "/usr/bin/git"
        (self.project_dir / ".git").mkdir()

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "abc1234 1 1 1\nauthor John Doe\nauthor-mail <john@example.com>\nauthor-time 1600000000\n"
        mock_run.return_value = mock_process

        info = get_todo_blame(self.project_dir, "file.py", 10)

        self.assertEqual(info['author'], "John Doe")
        self.assertEqual(info['commit'], "abc1234")
        # 1600000000 is approx 2020-09-13
        self.assertIn("2020", info['date'])

if __name__ == '__main__':
    unittest.main()
