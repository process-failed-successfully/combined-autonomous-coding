
import unittest
from unittest.mock import patch, MagicMock
import argparse
from pathlib import Path
import tempfile
import shutil
import subprocess

from main import run_next

class TestNextCommand(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        # Initialize a git repo
        subprocess.run(["git", "init"], cwd=self.project_dir, capture_output=True)
        (self.project_dir / "test.txt").write_text("initial commit")
        subprocess.run(["git", "add", "."], cwd=self.project_dir, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.project_dir, capture_output=True)


    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('main.get_suggestions')
    @patch('builtins.input', return_value='y')
    @patch('subprocess.run')
    def test_next_with_suggestion_and_confirmation(self, mock_subprocess_run, mock_input, mock_get_suggestions):
        mock_subprocess_run.return_value = MagicMock(returncode=0)
        mock_get_suggestions.return_value = [{'command': '`./main.py commit -m "commit message"`', 'reason': 'Uncommitted changes'}]
        args = argparse.Namespace(project_dir=self.project_dir, yes=False)

        with self.assertRaises(SystemExit) as cm:
            run_next(args)

        self.assertEqual(cm.exception.code, 0)
        mock_get_suggestions.assert_called_once_with(project_dir=self.project_dir, limit=1)
        mock_input.assert_called_once()
        mock_subprocess_run.assert_called_once_with(['./main.py', 'commit', '-m', 'commit message'], cwd=self.project_dir)

    @patch('main.get_suggestions')
    @patch('builtins.input', return_value='n')
    @patch('subprocess.run')
    def test_next_with_suggestion_and_rejection(self, mock_subprocess_run, mock_input, mock_get_suggestions):
        mock_get_suggestions.return_value = [{'command': '`./main.py test`', 'reason': 'Ready for testing'}]
        args = argparse.Namespace(project_dir=self.project_dir, yes=False)

        with self.assertRaises(SystemExit) as cm:
            run_next(args)

        self.assertEqual(cm.exception.code, 0)
        mock_get_suggestions.assert_called_once_with(project_dir=self.project_dir, limit=1)
        mock_input.assert_called_once()
        mock_subprocess_run.assert_not_called()

    @patch('main.get_suggestions')
    @patch('subprocess.run')
    def test_next_with_yes_flag(self, mock_subprocess_run, mock_get_suggestions):
        mock_subprocess_run.return_value = MagicMock(returncode=0)
        mock_get_suggestions.return_value = [{'command': '`./main.py pr create --title "feat: new feature"`', 'reason': 'Ready for PR'}]
        args = argparse.Namespace(project_dir=self.project_dir, yes=True)

        with self.assertRaises(SystemExit) as cm:
            run_next(args)

        self.assertEqual(cm.exception.code, 0)
        mock_get_suggestions.assert_called_once_with(project_dir=self.project_dir, limit=1)
        mock_subprocess_run.assert_called_once_with(['./main.py', 'pr', 'create', '--title', 'feat: new feature'], cwd=self.project_dir)

    @patch('main.get_suggestions')
    def test_next_with_no_suggestions(self, mock_get_suggestions):
        mock_get_suggestions.return_value = []
        args = argparse.Namespace(project_dir=self.project_dir, yes=False)

        with self.assertRaises(SystemExit) as cm:
            run_next(args)

        self.assertEqual(cm.exception.code, 0)
        mock_get_suggestions.assert_called_once_with(project_dir=self.project_dir, limit=1)

if __name__ == '__main__':
    unittest.main()
