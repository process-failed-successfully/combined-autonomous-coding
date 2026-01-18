
import unittest
import subprocess
import tempfile
import shutil
import sys
import os
from pathlib import Path

# Adjust the path to import from the root of the project
sys.path.insert(0, str(Path(__file__).parent.parent))

class TestMainRelease(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory and a git repository."""
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        self.git_path = shutil.which("git")
        self.main_path = Path(__file__).parent.parent / "main.py"

        if not self.git_path:
            self.fail("Git executable not found in PATH")

        # Initialize a git repository
        subprocess.run([self.git_path, "init", "-b", "main"], cwd=self.project_dir, check=True)
        subprocess.run([self.git_path, "config", "user.name", "Test User"], cwd=self.project_dir, check=True)
        subprocess.run([self.git_path, "config", "user.email", "test@example.com"], cwd=self.project_dir, check=True)

        # Create a package.json
        (self.project_dir / "package.json").write_text('{"version": "1.0.0"}')
        self._commit_file("package.json", '{"version": "1.0.0"}', "chore: initial commit")

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.test_dir)

    def _commit_file(self, filename, content, message):
        """Helper to write a file and commit it."""
        (self.project_dir / filename).write_text(content)
        subprocess.run([self.git_path, "add", filename], cwd=self.project_dir, check=True)
        subprocess.run([self.git_path, "commit", "-m", message], cwd=self.project_dir, check=True)

    def run_cli(self, args):
        """Helper to run the CLI."""
        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path(__file__).parent.parent)
        result = subprocess.run(
            [sys.executable, str(self.main_path)] + args,
            cwd=self.project_dir,
            capture_output=True,
            text=True,
            env=env
        )
        return result

    def test_release_plan_no_bump(self):
        """Test 'release plan' with no significant changes."""
        # No new commits after initial commit (which was chore)
        result = self.run_cli(["release", "plan"])

        self.assertEqual(result.returncode, 0)
        self.assertIn("No version bump required", result.stdout)

    def test_release_plan_minor_bump(self):
        """Test 'release plan' with a feature commit."""
        self._commit_file("feature.txt", "feature", "feat: added feature")

        result = self.run_cli(["release", "plan"])

        self.assertEqual(result.returncode, 0)
        self.assertIn("Current version (file/tag): 1.0.0", result.stdout)
        self.assertIn("Next version (calculated): 1.1.0", result.stdout)
        self.assertIn("## Features", result.stdout)
        self.assertIn("- feat: added feature", result.stdout)

    def test_release_apply_tag(self):
        """Test 'release apply' creates a tag."""
        self._commit_file("fix.txt", "fix", "fix: bug fix")

        # Run apply
        result = self.run_cli(["release", "apply", "--yes"])

        self.assertEqual(result.returncode, 0)
        self.assertIn("Next version (calculated): 1.0.1", result.stdout)
        self.assertIn("Created tag: v1.0.1", result.stdout)

        # Verify tag exists
        tag_check = subprocess.run(
            [self.git_path, "tag", "-l", "v1.0.1"],
            cwd=self.project_dir,
            capture_output=True,
            text=True
        )
        self.assertIn("v1.0.1", tag_check.stdout)

        # Verify file update
        pkg_json = (self.project_dir / "package.json").read_text()
        self.assertIn('"version": "1.0.1"', pkg_json)

    def test_release_force_version(self):
        """Test 'release --force-version'."""
        result = self.run_cli(["release", "plan", "--force-version", "2.0.0"])

        self.assertEqual(result.returncode, 0)
        self.assertIn("Next version (forced): 2.0.0", result.stdout)

if __name__ == '__main__':
    unittest.main()
