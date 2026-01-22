
from main import run_test
import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path
import tempfile
import shutil
import argparse

# It's necessary to add the project root to the path for the import to work
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestMainTestSubcommand(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def _create_mock_args(self, test_args=None):
        if test_args is None:
            test_args = []
        return argparse.Namespace(
            project_dir=self.project_dir,
            test_args=test_args
        )

    @patch('main.subprocess.run')
    @patch('main.shutil.which', return_value='/usr/bin/npm')
    def test_detects_and_runs_npm(self, mock_which, mock_run):
        (self.project_dir / "package.json").touch()
        args = self._create_mock_args()
        mock_run.return_value = MagicMock(returncode=0)

        with self.assertRaises(SystemExit) as cm:
            run_test(args)
        self.assertEqual(cm.exception.code, 0)

        mock_run.assert_called_once_with(['npm', 'test'], cwd=self.project_dir)

    @patch('main.subprocess.run')
    @patch('main.shutil.which', return_value='/usr/bin/pytest')
    def test_detects_and_runs_pytest(self, mock_which, mock_run):
        (self.project_dir / "pyproject.toml").touch()
        args = self._create_mock_args()
        mock_run.return_value = MagicMock(returncode=0)

        with self.assertRaises(SystemExit) as cm:
            run_test(args)
        self.assertEqual(cm.exception.code, 0)

        mock_run.assert_called_once_with(['pytest'], cwd=self.project_dir)

    @patch('main.subprocess.run')
    @patch('main.shutil.which', return_value=None)  # Mock that pytest is not found
    def test_falls_back_to_unittest(self, mock_which, mock_run):
        (self.project_dir / "requirements.txt").touch()
        args = self._create_mock_args()
        mock_run.return_value = MagicMock(returncode=0)

        with self.assertRaises(SystemExit) as cm:
            run_test(args)
        self.assertEqual(cm.exception.code, 0)

        mock_run.assert_called_once_with([sys.executable, '-m', 'unittest', 'discover'], cwd=self.project_dir)

    @patch('main.subprocess.run')
    @patch('main.shutil.which', return_value='/usr/bin/go')
    def test_detects_and_runs_go(self, mock_which, mock_run):
        (self.project_dir / "go.mod").touch()
        args = self._create_mock_args()
        mock_run.return_value = MagicMock(returncode=0)

        with self.assertRaises(SystemExit) as cm:
            run_test(args)
        self.assertEqual(cm.exception.code, 0)

        mock_run.assert_called_once_with(['go', 'test', './...'], cwd=self.project_dir)

    @patch('main.subprocess.run')
    def test_unrecognized_project_type(self, mock_run):
        args = self._create_mock_args()
        with self.assertRaises(SystemExit) as cm:
            run_test(args)
        self.assertEqual(cm.exception.code, 1)
        mock_run.assert_not_called()

    @patch('main.subprocess.run')
    @patch('main.shutil.which', return_value='/usr/bin/npm')
    def test_passthrough_arguments_for_npm(self, mock_which, mock_run):
        (self.project_dir / "package.json").touch()
        test_args = ['--watch', 'my-test.js']
        args = self._create_mock_args(test_args=test_args)
        mock_run.return_value = MagicMock(returncode=0)

        with self.assertRaises(SystemExit):
            run_test(args)

        mock_run.assert_called_once_with(['npm', 'test', '--', '--watch', 'my-test.js'], cwd=self.project_dir)

    @patch('main.subprocess.run')
    @patch('main.shutil.which', return_value='/usr/bin/pytest')
    def test_passthrough_arguments_for_pytest(self, mock_which, mock_run):
        (self.project_dir / "pyproject.toml").touch()
        test_args = ['-k', 'specific_test', '--verbose']
        args = self._create_mock_args(test_args=test_args)

        with self.assertRaises(SystemExit):
            run_test(args)

        mock_run.assert_called_once_with(['pytest', '-k', 'specific_test', '--verbose'], cwd=self.project_dir)


if __name__ == '__main__':
    unittest.main()
