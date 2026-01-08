import unittest
from unittest.mock import patch, MagicMock
import subprocess
from pathlib import Path
import tempfile
import shutil
import sys
from argparse import Namespace

# Make sure the main script can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from main import run_format

class TestFormatCommand(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def create_py_project(self, unformatted_code):
        (self.project_dir / "pyproject.toml").touch()
        (self.project_dir / "main.py").write_text(unformatted_code)

    def create_js_project(self, unformatted_code):
        (self.project_dir / "package.json").touch()
        (self.project_dir / "index.js").write_text(unformatted_code)

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_format_python_project(self, mock_subprocess_run, mock_shutil_which):
        unformatted_code = "def my_func():\n  pass"
        self.create_py_project(unformatted_code)

        mock_shutil_which.return_value = "/usr/bin/black"
        mock_subprocess_run.return_value = MagicMock(returncode=0)

        args = Namespace(
            project_dir=self.project_dir,
            check=False,
            format_args=[]
        )

        with self.assertRaises(SystemExit) as cm:
            run_format(args)

        self.assertEqual(cm.exception.code, 0)
        mock_subprocess_run.assert_called_once_with(
            ["black", "."], cwd=self.project_dir
        )

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_format_python_project_check_mode(self, mock_subprocess_run, mock_shutil_which):
        unformatted_code = "def my_func():\n  pass"
        self.create_py_project(unformatted_code)

        mock_shutil_which.return_value = "/usr/bin/black"
        mock_subprocess_run.return_value = MagicMock(returncode=1)

        args = Namespace(
            project_dir=self.project_dir,
            check=True,
            format_args=[]
        )

        with self.assertRaises(SystemExit) as cm:
            run_format(args)

        self.assertEqual(cm.exception.code, 1)
        mock_subprocess_run.assert_called_once_with(
            ["black", ".", "--check"], cwd=self.project_dir
        )

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_format_js_project(self, mock_subprocess_run, mock_shutil_which):
        unformatted_code = "const x = 1"
        self.create_js_project(unformatted_code)

        mock_shutil_which.return_value = "prettier"
        mock_subprocess_run.return_value = MagicMock(returncode=0)

        args = Namespace(
            project_dir=self.project_dir,
            check=False,
            format_args=[]
        )

        with self.assertRaises(SystemExit) as cm:
            run_format(args)

        self.assertEqual(cm.exception.code, 0)
        mock_subprocess_run.assert_called_once_with(
            ["prettier", ".", "--write"], cwd=self.project_dir
        )

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_format_js_project_check_mode(self, mock_subprocess_run, mock_shutil_which):
        unformatted_code = "const x = 1"
        self.create_js_project(unformatted_code)

        mock_shutil_which.return_value = "prettier"
        mock_subprocess_run.return_value = MagicMock(returncode=1)

        args = Namespace(
            project_dir=self.project_dir,
            check=True,
            format_args=[]
        )

        with self.assertRaises(SystemExit) as cm:
            run_format(args)

        self.assertEqual(cm.exception.code, 1)
        mock_subprocess_run.assert_called_once_with(
            ["prettier", ".", "--check"], cwd=self.project_dir
        )

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_no_formatter_found(self, mock_subprocess_run, mock_shutil_which):
        unformatted_code = "def my_func():\n  pass"
        self.create_py_project(unformatted_code)

        mock_shutil_which.return_value = None

        args = Namespace(
            project_dir=self.project_dir,
            check=False,
            format_args=[]
        )

        with self.assertRaises(SystemExit) as cm:
            run_format(args)

        self.assertEqual(cm.exception.code, 1)
        mock_subprocess_run.assert_not_called()

if __name__ == "__main__":
    unittest.main()
