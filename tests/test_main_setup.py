from main import run_setup
import unittest
from unittest.mock import patch, call
import sys
import argparse
from pathlib import Path
import tempfile
import shutil
from io import StringIO

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestSetupCommand(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    @patch('main.subprocess.run')
    @patch('main.shutil.which', return_value='/usr/bin/pip')
    def test_python_project(self, mock_which, mock_run):
        (self.project_dir / "requirements.txt").touch()
        args = argparse.Namespace(project_dir=self.project_dir)

        mock_run.return_value.returncode = 0
        with self.assertRaises(SystemExit) as cm:
            run_setup(args)
        self.assertEqual(cm.exception.code, 0)

        expected_command = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
        mock_run.assert_called_once_with(expected_command, cwd=self.project_dir)

    @patch('main.subprocess.run')
    @patch('main.shutil.which', return_value='/usr/bin/pip')
    def test_python_project_with_dev(self, mock_which, mock_run):
        (self.project_dir / "requirements.txt").touch()
        (self.project_dir / "requirements-dev.txt").touch()
        args = argparse.Namespace(project_dir=self.project_dir)

        # Mock successful return codes for both calls
        mock_run.return_value.returncode = 0

        with self.assertRaises(SystemExit) as cm:
            run_setup(args)
        self.assertEqual(cm.exception.code, 0)

        dev_command = [sys.executable, "-m", "pip", "install", "-r", "requirements-dev.txt"]
        main_command = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]

        calls = [
            call(dev_command, cwd=self.project_dir),
            call(main_command, cwd=self.project_dir)
        ]
        mock_run.assert_has_calls(calls, any_order=False)
        self.assertEqual(mock_run.call_count, 2)

    @patch('main.subprocess.run')
    @patch('main.shutil.which', side_effect=lambda x: f'/usr/bin/{x}' if x == 'npm' else None)
    def test_npm_project(self, mock_which, mock_run):
        (self.project_dir / "package.json").touch()
        (self.project_dir / "package-lock.json").touch()
        args = argparse.Namespace(project_dir=self.project_dir)

        mock_run.return_value.returncode = 0
        with self.assertRaises(SystemExit) as cm:
            run_setup(args)
        self.assertEqual(cm.exception.code, 0)

        mock_run.assert_called_once_with(["npm", "install"], cwd=self.project_dir)

    @patch('main.subprocess.run')
    @patch('main.shutil.which', side_effect=lambda x: f'/usr/bin/{x}' if x == 'yarn' else None)
    def test_yarn_project(self, mock_which, mock_run):
        (self.project_dir / "package.json").touch()
        (self.project_dir / "yarn.lock").touch()
        args = argparse.Namespace(project_dir=self.project_dir)

        mock_run.return_value.returncode = 0
        with self.assertRaises(SystemExit) as cm:
            run_setup(args)
        self.assertEqual(cm.exception.code, 0)

        mock_run.assert_called_once_with(["yarn", "install"], cwd=self.project_dir)

    @patch('main.subprocess.run')
    @patch('main.shutil.which', side_effect=lambda x: f'/usr/bin/{x}' if x == 'pnpm' else None)
    def test_pnpm_project(self, mock_which, mock_run):
        (self.project_dir / "package.json").touch()
        (self.project_dir / "pnpm-lock.yaml").touch()
        args = argparse.Namespace(project_dir=self.project_dir)

        mock_run.return_value.returncode = 0
        with self.assertRaises(SystemExit) as cm:
            run_setup(args)
        self.assertEqual(cm.exception.code, 0)

        mock_run.assert_called_once_with(["pnpm", "install"], cwd=self.project_dir)

    @patch('main.subprocess.run')
    @patch('main.shutil.which', return_value='/usr/bin/go')
    def test_go_project(self, mock_which, mock_run):
        (self.project_dir / "go.mod").touch()
        args = argparse.Namespace(project_dir=self.project_dir)

        mock_run.return_value.returncode = 0
        with self.assertRaises(SystemExit) as cm:
            run_setup(args)
        self.assertEqual(cm.exception.code, 0)

        mock_run.assert_called_once_with(["go", "mod", "tidy"], cwd=self.project_dir)

    @patch('main.subprocess.run')
    @patch('sys.stderr', new_callable=StringIO)
    def test_no_project_found(self, mock_stderr, mock_run):
        args = argparse.Namespace(project_dir=self.project_dir)

        with self.assertRaises(SystemExit) as cm:
            run_setup(args)

        self.assertEqual(cm.exception.code, 1)
        self.assertIn("Could not detect a recognizable project type", mock_stderr.getvalue())
        mock_run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
