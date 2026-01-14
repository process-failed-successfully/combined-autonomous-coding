
import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path
import argparse
import tempfile
import subprocess
import os

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from main import run_patch

class TestPatchCommand(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.tmp_dir.name)
        subprocess.run(["git", "init"], cwd=self.project_dir)
        (self.project_dir / "test.txt").write_text("initial content\n")
        subprocess.run(["git", "add", "."], cwd=self.project_dir)
        subprocess.run(["git", "commit", "-m", "initial commit"], cwd=self.project_dir)

    def tearDown(self):
        self.tmp_dir.cleanup()

    @patch("main.shutil.which", return_value=None)
    @patch('builtins.print')
    def test_git_not_installed(self, mock_print, mock_which):
        args = argparse.Namespace(project_dir=self.project_dir, patch_file=None, reverse=False)
        with self.assertRaises(SystemExit) as e:
            run_patch(args)
        self.assertEqual(e.exception.code, 1)
        mock_print.assert_called_with("❌ Error: 'git' command not found. Please ensure Git is installed and in your PATH.", file=sys.stderr)

    def test_apply_patch_from_file(self):
        patch_content = "--- a/test.txt\n+++ b/test.txt\n@@ -1,1 +1,2 @@\n initial content\n+new line\n"
        patch_file = self.project_dir / "test.patch"
        patch_file.write_text(patch_content)
        args = argparse.Namespace(project_dir=self.project_dir, patch_file=str(patch_file), reverse=False)
        with self.assertRaises(SystemExit) as e:
            run_patch(args)
        self.assertEqual(e.exception.code, 0)
        self.assertEqual((self.project_dir / "test.txt").read_text(), "initial content\nnew line\n")

    def test_apply_patch_from_stdin(self):
        patch_content = "--- a/test.txt\n+++ b/test.txt\n@@ -1,1 +1,2 @@\n initial content\n+new line\n"
        args = argparse.Namespace(project_dir=self.project_dir, patch_file=None, reverse=False)
        with patch('sys.stdin', new=MagicMock()) as mock_stdin:
            mock_stdin.read.return_value = patch_content
            with self.assertRaises(SystemExit) as e:
                run_patch(args)
            self.assertEqual(e.exception.code, 0)
        self.assertEqual((self.project_dir / "test.txt").read_text(), "initial content\nnew line\n")

    def test_reverse_patch(self):
        patch_content = "--- a/test.txt\n+++ b/test.txt\n@@ -1,1 +1,2 @@\n initial content\n+new line\n"
        patch_file = self.project_dir / "test.patch"
        patch_file.write_text(patch_content)
        (self.project_dir / "test.txt").write_text("initial content\nnew line\n")
        args = argparse.Namespace(project_dir=self.project_dir, patch_file=str(patch_file), reverse=True)
        with self.assertRaises(SystemExit) as e:
            run_patch(args)
        self.assertEqual(e.exception.code, 0)
        self.assertEqual((self.project_dir / "test.txt").read_text(), "initial content\n")

    @patch('builtins.print')
    def test_patch_apply_fails(self, mock_print):
        patch_content = "invalid patch content"
        patch_file = self.project_dir / "test.patch"
        patch_file.write_text(patch_content)
        args = argparse.Namespace(project_dir=self.project_dir, patch_file=str(patch_file), reverse=False)
        with self.assertRaises(SystemExit) as e:
            run_patch(args)
        self.assertEqual(e.exception.code, 1)
        mock_print.assert_any_call("❌ Error applying patch:", file=sys.stderr)

if __name__ == "__main__":
    unittest.main()
