import unittest
from unittest.mock import patch, call, MagicMock
from pathlib import Path
import subprocess
import argparse
import sys

from main import run_review

class TestMainReview(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory for the project
        self.project_dir = Path("test_project")
        self.project_dir.mkdir(exist_ok=True)
        (self.project_dir / ".git").mkdir(exist_ok=True)
        (self.project_dir / "COMPLETED").touch()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.project_dir)

    @patch('main.run_test')
    @patch('builtins.input', side_effect=['a'])
    @patch('subprocess.run')
    @patch('shutil.which', return_value='/usr/bin/git')
    def test_review_approve(self, mock_which, mock_subprocess_run, mock_input, mock_run_test):
        args = argparse.Namespace(project_dir=self.project_dir)

        with self.assertRaises(SystemExit) as cm:
            run_review(args)

        self.assertEqual(cm.exception.code, 0)
        mock_run_test.assert_called_once()
        mock_subprocess_run.assert_called_with(['/usr/bin/git', '-C', str(self.project_dir.resolve()), 'diff', 'HEAD'])
        self.assertTrue((self.project_dir / "QA_PASSED").exists())

    @patch('main.run_test')
    @patch('builtins.input', side_effect=['r'])
    @patch('main._discard_all')
    @patch('subprocess.run')
    @patch('shutil.which', return_value='/usr/bin/git')
    def test_review_reject(self, mock_which, mock_subprocess_run, mock_discard_all, mock_input, mock_run_test):
        args = argparse.Namespace(project_dir=self.project_dir)

        with self.assertRaises(SystemExit) as cm:
            run_review(args)

        self.assertEqual(cm.exception.code, 0)
        mock_run_test.assert_called_once()
        mock_subprocess_run.assert_called_with(['/usr/bin/git', '-C', str(self.project_dir.resolve()), 'diff', 'HEAD'])
        mock_discard_all.assert_called_once_with(self.project_dir.resolve(), '/usr/bin/git', yes=True)
        self.assertFalse((self.project_dir / "COMPLETED").exists())

    @patch('main.run_test', side_effect=SystemExit(1))
    def test_review_tests_fail(self, mock_run_test):
        args = argparse.Namespace(project_dir=self.project_dir)

        with self.assertRaises(SystemExit) as cm:
            run_review(args)

        self.assertEqual(cm.exception.code, 1)
        mock_run_test.assert_called_once()
        self.assertFalse((self.project_dir / "QA_PASSED").exists())

if __name__ == '__main__':
    unittest.main()
