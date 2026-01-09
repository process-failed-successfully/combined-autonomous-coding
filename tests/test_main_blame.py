
import unittest
from unittest.mock import patch
import subprocess
import tempfile
import shutil
from pathlib import Path

# Adjust the path to import from the root of the project
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.cli_utils import _run_blame_logic

class TestMainBlame(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory and a git repository."""
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        self.git_path = shutil.which("git")

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
        # Get the commit hash
        result = subprocess.run([self.git_path, "rev-parse", "HEAD"], cwd=self.project_dir, check=True, capture_output=True, text=True)
        return result.stdout.strip()

    def test_blame_with_run_id(self):
        """Test blaming a file where a commit has a Run ID."""
        # First commit (manual)
        self._commit_file("test.txt", "line 1\n", "Initial commit")

        # Second commit (from agent)
        agent_commit_msg = "Agent modification\n\nRun ID: 20240101-120000-test-agent"
        self._commit_file("test.txt", "line 1\nline 2\n", agent_commit_msg)

        # Run the blame logic
        blame_output = _run_blame_logic(self.project_dir, self.project_dir / "test.txt")

        # Assertions
        self.assertIn("Run ID: 20240101-120000-test-agent", blame_output)
        self.assertIn("line 2", blame_output)
        self.assertIn("Author: Test User", blame_output) # The first line should still have the author
        self.assertIn("line 1", blame_output)

    def test_blame_without_run_id(self):
        """Test blaming a file where commits are made by a human author."""
        # First commit
        self._commit_file("test.txt", "hello\n", "First commit")

        # Second commit
        self._commit_file("test.txt", "hello\nworld\n", "Second commit")

        # Run the blame logic
        blame_output = _run_blame_logic(self.project_dir, self.project_dir / "test.txt")

        # Assertions
        self.assertNotIn("Run ID:", blame_output)
        self.assertIn("Author: Test User", blame_output)
        self.assertIn(": hello", blame_output)
        self.assertIn(": world", blame_output)

    def test_blame_on_non_existent_file(self):
        """Test that blame returns an error for a file that does not exist."""
        blame_output = _run_blame_logic(self.project_dir, self.project_dir / "nonexistent.txt")
        self.assertIn("❌ Error: File not found", blame_output)

    def test_blame_on_non_git_repository(self):
        """Test that blame returns an error when not in a git repository."""
        non_git_dir = tempfile.mkdtemp()
        try:
            blame_output = _run_blame_logic(Path(non_git_dir), Path(non_git_dir) / "some.txt")
            self.assertIn("❌ Error: Not a git repository", blame_output)
        finally:
            shutil.rmtree(non_git_dir)

    def test_blame_with_mixed_commits(self):
        """Test a file with a mix of agent and manual commits."""
        # Manual commit
        hash1 = self._commit_file("mix.txt", "manual line 1\n", "Manual work")

        # Agent commit
        agent_msg = "Agent work\n\nRun ID: agent-run-123"
        hash2 = self._commit_file("mix.txt", "manual line 1\nagent line 2\n", agent_msg)

        # Another manual commit
        hash3 = self._commit_file("mix.txt", "manual line 1\nagent line 2\nmanual line 3\n", "More manual work")

        # Run blame
        blame_output = _run_blame_logic(self.project_dir, self.project_dir / "mix.txt")
        lines = blame_output.split('\n')

        # Assertions
        self.assertEqual(len(lines), 3)
        self.assertIn(f"{hash1[:8]} (Author: Test User", lines[0])
        self.assertIn("manual line 1", lines[0])

        self.assertIn(f"{hash2[:8]} (Run ID: agent-run-123", lines[1])
        self.assertIn("agent line 2", lines[1])

        self.assertIn(f"{hash3[:8]} (Author: Test User", lines[2])
        self.assertIn("manual line 3", lines[2])


if __name__ == '__main__':
    unittest.main()
