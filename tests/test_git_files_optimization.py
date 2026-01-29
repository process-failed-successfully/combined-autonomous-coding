import unittest
import tempfile
import shutil
import subprocess
from pathlib import Path
import os
import sys

# Ensure shared module is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.git import get_all_git_files

class TestGitFilesOptimization(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.test_dir.name)
        self.git_setup()

    def tearDown(self):
        self.test_dir.cleanup()

    def git_setup(self):
        # Init repo
        subprocess.run(["git", "init"], cwd=self.project_dir, check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["git", "config", "user.email", "you@example.com"], cwd=self.project_dir, check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["git", "config", "user.name", "Your Name"], cwd=self.project_dir, check=True, stdout=subprocess.DEVNULL)

        # 1. Tracked file
        (self.project_dir / "tracked.txt").write_text("tracked")
        subprocess.run(["git", "add", "tracked.txt"], cwd=self.project_dir, check=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=self.project_dir, check=True, stdout=subprocess.DEVNULL)

        # 2. Untracked file
        (self.project_dir / "untracked.txt").write_text("untracked")

        # 3. Ignored file
        (self.project_dir / ".gitignore").write_text("ignored.txt\n")
        (self.project_dir / "ignored.txt").write_text("ignored")

        # 4. Force tracked ignored file
        (self.project_dir / "forced_ignored.txt").write_text("forced")
        with open(self.project_dir / ".gitignore", "a") as f:
            f.write("forced_ignored.txt\n")
        subprocess.run(["git", "add", "-f", "forced_ignored.txt"], cwd=self.project_dir, check=True)
        subprocess.run(["git", "commit", "-m", "forced"], cwd=self.project_dir, check=True, stdout=subprocess.DEVNULL)

    def test_get_all_git_files(self):
        files = get_all_git_files(self.project_dir)

        # Expected:
        # tracked.txt
        # untracked.txt
        # forced_ignored.txt
        # .gitignore

        # Not expected:
        # ignored.txt

        self.assertIn("tracked.txt", files)
        self.assertIn("untracked.txt", files)
        self.assertIn("forced_ignored.txt", files)
        self.assertIn(".gitignore", files)

        self.assertNotIn("ignored.txt", files)

        self.assertEqual(len(files), 4)

if __name__ == "__main__":
    unittest.main()
