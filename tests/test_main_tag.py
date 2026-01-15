
import unittest
from unittest.mock import patch, MagicMock
import subprocess
from pathlib import Path
import shutil
import os
import sys
from io import StringIO

# Add the root directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from main import run_tag

class TestRunTag(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("./test_project")
        self.test_dir.mkdir(exist_ok=True)
        self.git_path = shutil.which("git")
        subprocess.run([self.git_path, "init"], cwd=self.test_dir, capture_output=True)
        (self.test_dir / "test.txt").write_text("initial commit")
        subprocess.run([self.git_path, "add", "test.txt"], cwd=self.test_dir, capture_output=True)
        subprocess.run([self.git_path, "commit", "-m", "Initial commit"], cwd=self.test_dir, capture_output=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_create_lightweight_tag(self):
        args = MagicMock()
        args.action = "create"
        args.tag_name = "v1.0"
        args.message = None
        args.commit = None
        args.project_dir = self.test_dir

        run_tag(args)

        result = subprocess.run([self.git_path, "tag"], cwd=self.test_dir, capture_output=True, text=True)
        self.assertIn("v1.0", result.stdout)

    def test_create_annotated_tag(self):
        args = MagicMock()
        args.action = "create"
        args.tag_name = "v1.1"
        args.message = "Annotated tag"
        args.commit = None
        args.project_dir = self.test_dir

        run_tag(args)

        result = subprocess.run([self.git_path, "show", "v1.1"], cwd=self.test_dir, capture_output=True, text=True)
        self.assertIn("Annotated tag", result.stdout)

    def test_list_tags(self):
        subprocess.run([self.git_path, "tag", "v0.1"], cwd=self.test_dir)
        subprocess.run([self.git_path, "tag", "v0.2"], cwd=self.test_dir)

        args = MagicMock()
        args.action = "list"
        args.project_dir = self.test_dir
        args.tag_name = None

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            run_tag(args)
            output = mock_stdout.getvalue()

        self.assertIn("v0.1", output)
        self.assertIn("v0.2", output)

    def test_delete_tag(self):
        subprocess.run([self.git_path, "tag", "v0.3"], cwd=self.test_dir)

        args = MagicMock()
        args.action = "delete"
        args.tag_name = "v0.3"
        args.project_dir = self.test_dir

        run_tag(args)

        result = subprocess.run([self.git_path, "tag"], cwd=self.test_dir, capture_output=True, text=True)
        self.assertNotIn("v0.3", result.stdout)

    def test_create_tag_on_specific_commit(self):
        (self.test_dir / "test2.txt").write_text("second commit")
        subprocess.run([self.git_path, "add", "test2.txt"], cwd=self.test_dir)
        subprocess.run([self.git_path, "commit", "-m", "Second commit"], cwd=self.test_dir)

        initial_commit_hash = subprocess.run(
            [self.git_path, "rev-parse", "HEAD~1"],
            cwd=self.test_dir,
            capture_output=True,
            text=True
        ).stdout.strip()

        args = MagicMock()
        args.action = "create"
        args.tag_name = "initial-commit-tag"
        args.message = None
        args.commit = initial_commit_hash
        args.project_dir = self.test_dir

        run_tag(args)

        tag_commit_hash = subprocess.run(
            [self.git_path, "rev-parse", "initial-commit-tag"],
            cwd=self.test_dir,
            capture_output=True,
            text=True
        ).stdout.strip()

        self.assertEqual(initial_commit_hash, tag_commit_hash)

if __name__ == '__main__':
    unittest.main()
