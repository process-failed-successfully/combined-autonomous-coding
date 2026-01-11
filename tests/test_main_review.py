import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import argparse
import sys
from io import StringIO

from main import run_review

class TestRunReview(unittest.TestCase):

    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.project_dir.mkdir(exist_ok=True)
        (self.project_dir / "COMPLETED").touch()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.project_dir)

    @patch('main.run_test')
    @patch('main.run_diff')
    @patch('builtins.input', return_value='approve')
    def test_review_approve(self, mock_input, mock_run_diff, mock_run_test):
        args = argparse.Namespace(project_dir=self.project_dir)

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            with self.assertRaises(SystemExit) as cm:
                run_review(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertTrue((self.project_dir / "QA_PASSED").exists())
        self.assertIn("Work approved", mock_stdout.getvalue())

    @patch('main.run_test')
    @patch('main.run_diff')
    @patch('builtins.input', return_value='reject')
    def test_review_reject(self, mock_input, mock_run_diff, mock_run_test):
        args = argparse.Namespace(project_dir=self.project_dir)

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            with self.assertRaises(SystemExit) as cm:
                run_review(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertFalse((self.project_dir / "COMPLETED").exists())
        self.assertIn("Work rejected", mock_stdout.getvalue())

    def test_review_no_completed_file(self):
        (self.project_dir / "COMPLETED").unlink()
        args = argparse.Namespace(project_dir=self.project_dir)

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            with self.assertRaises(SystemExit) as cm:
                run_review(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertIn("Nothing to review", mock_stdout.getvalue())

    @patch('main.run_test', side_effect=SystemExit(1))
    @patch('main.run_diff')
    @patch('builtins.input', return_value='approve')
    def test_review_tests_fail(self, mock_input, mock_run_diff, mock_run_test):
        args = argparse.Namespace(project_dir=self.project_dir)

        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with self.assertRaises(SystemExit):
                run_review(args)

        self.assertIn("Tests failed", mock_stderr.getvalue())

if __name__ == '__main__':
    unittest.main()
