import unittest
from unittest.mock import patch, MagicMock
import sys
import io
from pathlib import Path
import tempfile
import shutil
import subprocess
import argparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import main

class TestMainTree(unittest.TestCase):
    def setUp(self):
        self.original_stdout = sys.stdout
        sys.stdout = self.captured_output = io.StringIO()
        self.test_dir = tempfile.mkdtemp()
        self.project_path = Path(self.test_dir)

    def tearDown(self):
        sys.stdout = self.original_stdout
        shutil.rmtree(self.test_dir)

    def run_tree(self, depth=None, full=False, path=None):
        path = path if path is not None else self.project_path
        args = argparse.Namespace(project_dir=path, depth=depth, full=full)
        with self.assertRaises(SystemExit) as cm:
            main.run_tree(args)
        self.assertEqual(cm.exception.code, 0)
        return self.captured_output.getvalue().strip()

    def create_structure(self):
        (self.project_path / "dir1").mkdir()
        (self.project_path / "dir2").mkdir()
        (self.project_path / "file1.txt").touch()
        (self.project_path / "dir1" / "file2.txt").touch()
        (self.project_path / "dir1" / "subdir").mkdir()
        (self.project_path / "dir1" / "subdir" / "file3.txt").touch()

    def test_tree_basic_structure(self):
        self.create_structure()
        output = self.run_tree()
        expected = f"""{self.project_path.name}/
├── dir1/
│   ├── subdir/
│   │   └── file3.txt
│   └── file2.txt
├── dir2/
└── file1.txt"""
        self.assertEqual(output, expected)

    def test_tree_with_depth_limit(self):
        self.create_structure()
        output = self.run_tree(depth=1)
        expected = f"""{self.project_path.name}/
├── dir1/
├── dir2/
└── file1.txt"""
        self.assertEqual(output, expected)

    def test_tree_empty_directory(self):
        output = self.run_tree()
        self.assertEqual(output, f"{self.project_path.name}/")

    def test_tree_non_existent_directory(self):
        output = self.run_tree(path=Path("/non/existent/path"))
        self.assertIn("Error:", output)

    @patch('shared.cli_utils.shutil.which', return_value='/usr/bin/git')
    @patch('shared.cli_utils.subprocess.run')
    def test_tree_git_ignore(self, mock_subprocess_run, mock_shutil_which):
        (self.project_path / ".git").mkdir()
        self.create_structure()
        (self.project_path / "ignored_file.txt").touch()
        (self.project_path / "dir1" / "ignored_in_dir.log").touch()

        def side_effect(*args, **kwargs):
            cmd = args[0]
            if "check-ignore" in cmd:
                path_to_check = cmd[-1]
                if "ignored" in path_to_check:
                    return MagicMock(returncode=0)
            return MagicMock(returncode=1)

        mock_subprocess_run.side_effect = side_effect
        output = self.run_tree(full=False)
        self.assertNotIn("ignored_file.txt", output)
        self.assertNotIn("ignored_in_dir.log", output)
        self.assertIn("file1.txt", output)

    @patch('shared.cli_utils.shutil.which', return_value='/usr/bin/git')
    @patch('shared.cli_utils.subprocess.run')
    def test_tree_full_option(self, mock_subprocess_run, mock_shutil_which):
        (self.project_path / ".git").mkdir()
        self.create_structure()
        (self.project_path / "ignored_file.txt").touch()
        (self.project_path / "dir1" / "ignored_in_dir.log").touch()

        def side_effect(*args, **kwargs):
            cmd = args[0]
            if "check-ignore" in cmd:
                path_to_check = cmd[-1]
                if "ignored" in path_to_check:
                    return MagicMock(returncode=0)
            return MagicMock(returncode=1)
        mock_subprocess_run.side_effect = side_effect
        output = self.run_tree(full=True)
        self.assertIn("ignored_file.txt", output)
        self.assertIn("ignored_in_dir.log", output)

if __name__ == '__main__':
    unittest.main()
