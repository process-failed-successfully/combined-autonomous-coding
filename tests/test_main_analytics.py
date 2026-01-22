
import unittest
import subprocess
import tempfile
import shutil
import sys
import os
from pathlib import Path

# Adjust the path to import from the root of the project
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestMainAnalytics(unittest.TestCase):

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

    def test_analytics_git(self):
        """Test 'analytics git' command."""
        self._commit_file("test.py", "print('hello')", "Initial commit")
        self._commit_file("test.py", "print('world')", "Update test.py")
        self._commit_file("README.md", "# Test Project", "Add README")

        result = self.run_cli(["analytics", "git"])

        self.assertEqual(result.returncode, 0)
        self.assertIn("Git Analytics", result.stdout)
        self.assertIn("Top Contributors", result.stdout)
        self.assertIn("Test User", result.stdout)
        self.assertIn("Hotspots", result.stdout)
        self.assertIn("test.py", result.stdout)
        self.assertIn("Recent Activity", result.stdout)

    def test_analytics_code(self):
        """Test 'analytics code' command."""
        (self.project_dir / "src").mkdir()
        (self.project_dir / "src/main.py").write_text("print('main')")
        (self.project_dir / "src/utils.py").write_text("def utils(): pass")
        (self.project_dir / "README.md").write_text("# Readme")

        result = self.run_cli(["analytics", "code"])

        self.assertEqual(result.returncode, 0)
        self.assertIn("Agent Context Analysis by File Type", result.stdout)
        self.assertIn(".py", result.stdout)
        self.assertIn(".md", result.stdout)


if __name__ == '__main__':
    unittest.main()
