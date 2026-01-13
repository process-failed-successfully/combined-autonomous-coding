import unittest
from unittest.mock import patch, MagicMock
import argparse
from pathlib import Path
import sys

from main import run_setup

class TestMainSetup(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.project_dir.mkdir(exist_ok=True)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.project_dir)

    @patch("subprocess.run")
    def test_setup_python_project(self, mock_subprocess_run):
        mock_subprocess_run.return_value = MagicMock(returncode=0)
        (self.project_dir / "requirements.txt").touch()
        args = argparse.Namespace(project_dir=self.project_dir)

        with self.assertRaises(SystemExit) as cm:
            run_setup(args)

        self.assertEqual(cm.exception.code, 0)
        mock_subprocess_run.assert_called_with(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            cwd=self.project_dir
        )

    @patch("subprocess.run")
    def test_setup_python_project_with_dev(self, mock_subprocess_run):
        mock_subprocess_run.return_value = MagicMock(returncode=0)
        (self.project_dir / "requirements.txt").touch()
        (self.project_dir / "requirements-dev.txt").touch()
        args = argparse.Namespace(project_dir=self.project_dir)

        with self.assertRaises(SystemExit) as cm:
            run_setup(args)

        self.assertEqual(cm.exception.code, 0)
        mock_subprocess_run.assert_called_with(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-r", "requirements-dev.txt"],
            cwd=self.project_dir
        )

    @patch("subprocess.run")
    def test_setup_node_project_npm(self, mock_subprocess_run):
        mock_subprocess_run.return_value = MagicMock(returncode=0)
        (self.project_dir / "package.json").touch()
        args = argparse.Namespace(project_dir=self.project_dir)

        with self.assertRaises(SystemExit) as cm:
            run_setup(args)

        self.assertEqual(cm.exception.code, 0)
        mock_subprocess_run.assert_called_with(
            ["npm", "install"],
            cwd=self.project_dir
        )

    @patch("subprocess.run")
    def test_setup_node_project_yarn(self, mock_subprocess_run):
        mock_subprocess_run.return_value = MagicMock(returncode=0)
        (self.project_dir / "package.json").touch()
        (self.project_dir / "yarn.lock").touch()
        args = argparse.Namespace(project_dir=self.project_dir)

        with self.assertRaises(SystemExit) as cm:
            run_setup(args)

        self.assertEqual(cm.exception.code, 0)
        mock_subprocess_run.assert_called_with(
            ["yarn", "install"],
            cwd=self.project_dir
        )

    @patch("subprocess.run")
    def test_setup_node_project_pnpm(self, mock_subprocess_run):
        mock_subprocess_run.return_value = MagicMock(returncode=0)
        (self.project_dir / "package.json").touch()
        (self.project_dir / "pnpm-lock.yaml").touch()
        args = argparse.Namespace(project_dir=self.project_dir)

        with self.assertRaises(SystemExit) as cm:
            run_setup(args)

        self.assertEqual(cm.exception.code, 0)
        mock_subprocess_run.assert_called_with(
            ["pnpm", "install"],
            cwd=self.project_dir
        )

    @patch("subprocess.run")
    def test_setup_go_project(self, mock_subprocess_run):
        mock_subprocess_run.return_value = MagicMock(returncode=0)
        (self.project_dir / "go.mod").touch()
        args = argparse.Namespace(project_dir=self.project_dir)

        with self.assertRaises(SystemExit) as cm:
            run_setup(args)

        self.assertEqual(cm.exception.code, 0)
        mock_subprocess_run.assert_called_with(
            ["go", "mod", "tidy"],
            cwd=self.project_dir
        )

    @patch("subprocess.run")
    def test_setup_unknown_project(self, mock_subprocess_run):
        args = argparse.Namespace(project_dir=self.project_dir)

        with self.assertRaises(SystemExit) as cm:
            run_setup(args)

        self.assertEqual(cm.exception.code, 1)
        mock_subprocess_run.assert_not_called()

if __name__ == "__main__":
    unittest.main()
