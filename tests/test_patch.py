
import unittest
from unittest.mock import patch, MagicMock
import subprocess
from pathlib import Path
import sys

from main import run_patch

class TestPatchCommand(unittest.TestCase):

    def setUp(self):
        self.project_dir = Path("test_project")
        self.project_dir.mkdir(exist_ok=True)
        (self.project_dir / ".git").mkdir(exist_ok=True)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.project_dir)

    @patch("main.print")
    @patch("main.shutil.which")
    @patch("main.subprocess.run")
    def test_patch_from_file(self, mock_subprocess_run, mock_shutil_which, mock_print):
        mock_shutil_which.return_value = "/usr/bin/git"
        mock_subprocess_run.return_value = MagicMock(returncode=0)
        patch_file = self.project_dir / "test.patch"
        patch_file.write_text("test patch content")

        args = MagicMock()
        args.project_dir = self.project_dir
        args.patch_file = str(patch_file)
        args.reverse = False

        with self.assertRaises(SystemExit) as cm:
            run_patch(args)
        self.assertEqual(cm.exception.code, 0)

        mock_subprocess_run.assert_called_once_with(
            ["/usr/bin/git", "-C", str(self.project_dir.resolve()), "apply"],
            input="test patch content",
            text=True,
            capture_output=True
        )

    @patch("main.print")
    @patch("main.shutil.which")
    @patch("main.subprocess.run")
    @patch("sys.stdin")
    def test_patch_from_stdin(self, mock_stdin, mock_subprocess_run, mock_shutil_which, mock_print):
        mock_shutil_which.return_value = "/usr/bin/git"
        mock_subprocess_run.return_value = MagicMock(returncode=0)
        mock_stdin.read.return_value = "stdin patch content"

        args = MagicMock()
        args.project_dir = self.project_dir
        args.patch_file = None
        args.reverse = False

        with self.assertRaises(SystemExit) as cm:
            run_patch(args)
        self.assertEqual(cm.exception.code, 0)

        mock_subprocess_run.assert_called_once_with(
            ["/usr/bin/git", "-C", str(self.project_dir.resolve()), "apply"],
            input="stdin patch content",
            text=True,
            capture_output=True
        )

    @patch("main.print")
    @patch("main.shutil.which")
    @patch("main.subprocess.run")
    def test_patch_reverse(self, mock_subprocess_run, mock_shutil_which, mock_print):
        mock_shutil_which.return_value = "/usr/bin/git"
        mock_subprocess_run.return_value = MagicMock(returncode=0)
        patch_file = self.project_dir / "test.patch"
        patch_file.write_text("test patch content")

        args = MagicMock()
        args.project_dir = self.project_dir
        args.patch_file = str(patch_file)
        args.reverse = True

        with self.assertRaises(SystemExit) as cm:
            run_patch(args)
        self.assertEqual(cm.exception.code, 0)

        mock_subprocess_run.assert_called_once_with(
            ["/usr/bin/git", "-C", str(self.project_dir.resolve()), "apply", "--reverse"],
            input="test patch content",
            text=True,
            capture_output=True
        )

    @patch("main.print")
    @patch("main.shutil.which")
    def test_no_git(self, mock_shutil_which, mock_print):
        mock_shutil_which.return_value = None

        args = MagicMock()
        args.project_dir = self.project_dir
        args.patch_file = "dummy.patch"
        args.reverse = False

        with self.assertRaises(SystemExit) as cm:
            run_patch(args)

        self.assertEqual(cm.exception.code, 1)

    @patch("main.print")
    def test_no_git_repo(self, mock_print):
        import shutil
        shutil.rmtree(self.project_dir / ".git")

        args = MagicMock()
        args.project_dir = self.project_dir
        args.patch_file = "dummy.patch"
        args.reverse = False

        with self.assertRaises(SystemExit) as cm:
            run_patch(args)

        self.assertEqual(cm.exception.code, 1)

    @patch("main.print")
    @patch("main.shutil.which")
    def test_patch_file_not_found(self, mock_shutil_which, mock_print):
        mock_shutil_which.return_value = "/usr/bin/git"

        args = MagicMock()
        args.project_dir = self.project_dir
        args.patch_file = "non_existent.patch"
        args.reverse = False

        with self.assertRaises(SystemExit) as cm:
            run_patch(args)

        self.assertEqual(cm.exception.code, 1)

    @patch("main.print")
    @patch("main.shutil.which")
    @patch("main.subprocess.run")
    def test_patch_apply_error(self, mock_subprocess_run, mock_shutil_which, mock_print):
        mock_shutil_which.return_value = "/usr/bin/git"
        mock_subprocess_run.return_value = MagicMock(returncode=1, stderr="Git error")
        patch_file = self.project_dir / "test.patch"
        patch_file.write_text("test patch content")

        args = MagicMock()
        args.project_dir = self.project_dir
        args.patch_file = str(patch_file)
        args.reverse = False

        with self.assertRaises(SystemExit) as cm:
            run_patch(args)

        self.assertEqual(cm.exception.code, 1)

if __name__ == "__main__":
    unittest.main()
