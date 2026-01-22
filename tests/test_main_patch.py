import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from main import run_patch


class TestPatchCommand(unittest.TestCase):
    def setUp(self):
        self.project_dir = tempfile.TemporaryDirectory()
        self.project_path = Path(self.project_dir.name)
        subprocess.run(["git", "init"], cwd=self.project_path, check=True)
        (self.project_path / "test.txt").write_text("line1\nline2\n")
        subprocess.run(["git", "add", "test.txt"], cwd=self.project_path, check=True)
        subprocess.run(["git", "commit", "-m", "initial commit"], cwd=self.project_path, check=True)

    def tearDown(self):
        self.project_dir.cleanup()

    def test_run_patch_from_file(self):
        patch_file = self.project_path / "test.patch"
        patch_file.write_text("diff --git a/test.txt b/test.txt\n--- a/test.txt\n+++ b/test.txt\n@@ -1,2 +1,2 @@\n line1\n-line2\n+line2_modified\n")
        args = MagicMock(patch_file=patch_file, reverse=False, project_dir=self.project_path)

        with self.assertRaises(SystemExit) as cm:
            run_patch(args)
        self.assertEqual(cm.exception.code, 0)

        self.assertEqual((self.project_path / "test.txt").read_text(), "line1\nline2_modified\n")

    def test_run_patch_from_stdin(self):
        patch_content = "diff --git a/test.txt b/test.txt\n--- a/test.txt\n+++ b/test.txt\n@@ -1,2 +1,2 @@\n line1\n-line2\n+line2_stdin\n"
        with patch("sys.stdin.read", return_value=patch_content):
            args = MagicMock(patch_file=None, reverse=False, project_dir=self.project_path)

            with self.assertRaises(SystemExit) as cm:
                run_patch(args)
            self.assertEqual(cm.exception.code, 0)

        self.assertEqual((self.project_path / "test.txt").read_text(), "line1\nline2_stdin\n")

    def test_run_patch_reverse(self):
        (self.project_path / "test.txt").write_text("line1\nline2_modified\n")
        patch_file = self.project_path / "test.patch"
        patch_file.write_text("diff --git a/test.txt b/test.txt\n--- a/test.txt\n+++ b/test.txt\n@@ -1,2 +1,2 @@\n line1\n-line2\n+line2_modified\n")
        args = MagicMock(patch_file=patch_file, reverse=True, project_dir=self.project_path)

        with self.assertRaises(SystemExit) as cm:
            run_patch(args)
        self.assertEqual(cm.exception.code, 0)

        self.assertEqual((self.project_path / "test.txt").read_text(), "line1\nline2\n")

    def test_run_patch_invalid(self):
        patch_file = self.project_path / "test.patch"
        patch_file.write_text("invalid patch")
        args = MagicMock(patch_file=patch_file, reverse=False, project_dir=self.project_path)

        with self.assertRaises(SystemExit) as cm:
            run_patch(args)

        self.assertEqual(cm.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
