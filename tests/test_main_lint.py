from main import run_lint
import unittest
from unittest.mock import patch, MagicMock
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile

# Add the parent directory to the sys.path to allow imports from the 'shared' module
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestMainLint(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory for the project to be linted
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temp_dir.name)

    def tearDown(self):
        # Clean up the temporary directory
        self.temp_dir.cleanup()

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_lint_python_project_with_ruff(self, mock_which, mock_run):
        # Arrange
        (self.project_dir / "pyproject.toml").touch()
        mock_which.side_effect = lambda x: "/usr/bin/ruff" if x == "ruff" else None
        mock_run.return_value = MagicMock(returncode=0)
        args = argparse.Namespace(
            project_dir=self.project_dir,
            fix=False,
            lint_args=[]
        )

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_lint(args)

        # Assert
        self.assertEqual(cm.exception.code, 0)
        mock_run.assert_called_once_with(
            ["ruff", "check", "."],
            cwd=self.project_dir
        )

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_lint_python_project_with_ruff_fix(self, mock_which, mock_run):
        # Arrange
        (self.project_dir / "pyproject.toml").touch()
        mock_which.side_effect = lambda x: "/usr/bin/ruff" if x == "ruff" else None
        mock_run.return_value = MagicMock(returncode=0)
        args = argparse.Namespace(
            project_dir=self.project_dir,
            fix=True,
            lint_args=["--select", "F401"]
        )

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_lint(args)

        # Assert
        self.assertEqual(cm.exception.code, 0)
        mock_run.assert_called_once_with(
            ["ruff", "check", ".", "--fix", "--select", "F401"],
            cwd=self.project_dir
        )

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_lint_python_project_with_flake8(self, mock_which, mock_run):
        # Arrange
        (self.project_dir / "requirements.txt").touch()
        mock_which.side_effect = lambda x: "/usr/bin/flake8" if x == "flake8" else None
        mock_run.return_value = MagicMock(returncode=0)
        args = argparse.Namespace(
            project_dir=self.project_dir,
            fix=False,
            lint_args=[]
        )

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_lint(args)

        # Assert
        self.assertEqual(cm.exception.code, 0)
        mock_run.assert_called_once_with(
            ["flake8", "."],
            cwd=self.project_dir
        )

    @patch("builtins.print")
    @patch("subprocess.run")
    @patch("shutil.which")
    def test_lint_python_project_with_flake8_fix_shows_warning(self, mock_which, mock_run, mock_print):
        # Arrange
        (self.project_dir / "requirements.txt").touch()
        mock_which.side_effect = lambda x: "/usr/bin/flake8" if x == "flake8" else None
        args = argparse.Namespace(
            project_dir=self.project_dir,
            fix=True,
            lint_args=[]
        )

        # Act
        with self.assertRaises(SystemExit):
            run_lint(args)

        # Assert
        mock_print.assert_any_call("Warning: --fix is not supported by flake8. Ignoring.", file=sys.stderr)
        mock_run.assert_called_once_with(
            ["flake8", "."],
            cwd=self.project_dir
        )

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_lint_nodejs_project(self, mock_which, mock_run):
        # Arrange
        (self.project_dir / "package.json").write_text('{"scripts": {"lint": "eslint ."}}')
        mock_run.return_value = MagicMock(returncode=0)
        args = argparse.Namespace(
            project_dir=self.project_dir,
            fix=False,
            lint_args=[]
        )

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_lint(args)

        # Assert
        self.assertEqual(cm.exception.code, 0)
        mock_run.assert_called_once_with(
            ["npm", "run", "lint"],
            cwd=self.project_dir
        )

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_lint_nodejs_project_with_fix(self, mock_which, mock_run):
        # Arrange
        (self.project_dir / "package.json").write_text('{"scripts": {"lint": "eslint ."}}')
        mock_run.return_value = MagicMock(returncode=0)
        args = argparse.Namespace(
            project_dir=self.project_dir,
            fix=True,
            lint_args=[]
        )

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_lint(args)

        # Assert
        self.assertEqual(cm.exception.code, 0)
        mock_run.assert_called_once_with(
            ["npm", "run", "lint", "--", "--fix"],
            cwd=self.project_dir
        )

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_lint_nodejs_project_with_dedicated_fix_script(self, mock_which, mock_run):
        # Arrange
        (self.project_dir / "package.json").write_text('{"scripts": {"lint": "eslint .", "lint:fix": "eslint . --fix"}}')
        mock_run.return_value = MagicMock(returncode=0)
        args = argparse.Namespace(
            project_dir=self.project_dir,
            fix=True,
            lint_args=[]
        )

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_lint(args)

        # Assert
        self.assertEqual(cm.exception.code, 0)
        mock_run.assert_called_once_with(
            ["npm", "run", "lint:fix"],
            cwd=self.project_dir
        )

    @patch("builtins.print")
    def test_unrecognized_project_type(self, mock_print):
        # Arrange
        args = argparse.Namespace(
            project_dir=self.project_dir,
            fix=False,
            lint_args=[]
        )

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_lint(args)

        # Assert
        self.assertEqual(cm.exception.code, 1)
        mock_print.assert_any_call("❌ Error: Could not detect a recognizable project type or find a suitable linter.", file=sys.stderr)

    @patch("subprocess.run")
    def test_linter_fails(self, mock_run):
        # Arrange
        (self.project_dir / "pyproject.toml").touch()
        # Simulate a linter that finds issues and returns a non-zero exit code
        mock_run.return_value = subprocess.CompletedProcess(args=["ruff", "check", "."], returncode=1)
        with patch("shutil.which", return_value="/usr/bin/ruff"):
            args = argparse.Namespace(
                project_dir=self.project_dir,
                fix=False,
                lint_args=[]
            )

            # Act
            with self.assertRaises(SystemExit) as cm:
                run_lint(args)

            # Assert
            self.assertEqual(cm.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
