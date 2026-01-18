import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import subprocess
from pathlib import Path
import shutil
import os
import sys

# Add the root of the project to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.bisect import run_bisect_logic, analyze_commit

class TestBisect(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        """Set up a temporary git repository for testing."""
        self.test_dir = Path("test_repo_bisect")
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir(exist_ok=True)

        subprocess.run(["git", "init", "-b", "main"], cwd=self.test_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.test_dir, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.test_dir, check=True)

        self.commits = []

        # Commit 1 (Good)
        (self.test_dir / "file.txt").write_text("v1")
        self._commit("v1")

        # Commit 2 (Good)
        (self.test_dir / "file.txt").write_text("v2")
        self._commit("v2")

        # Commit 3 (Bad - introduces bug)
        (self.test_dir / "file.txt").write_text("v3_bug")
        self._commit("v3_bug")

        # Commit 4 (Bad)
        (self.test_dir / "file.txt").write_text("v4")
        self._commit("v4")

    def _commit(self, msg):
        subprocess.run(["git", "add", "."], cwd=self.test_dir, check=True)
        subprocess.run(["git", "commit", "-m", msg], cwd=self.test_dir, check=True)
        h = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.test_dir, capture_output=True, text=True, check=True).stdout.strip()
        self.commits.append(h)

    def tearDown(self):
        """Remove the temporary directory."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    @patch('shared.bisect.GeminiAgent')
    async def test_bisect_run(self, MockAgent):
        """Test the automated bisect flow."""
        # Setup mock agent
        mock_agent_instance = MockAgent.return_value
        mock_agent_instance.run_agent_session = AsyncMock(return_value=(True, "Analysis result", []))

        # We need a test script that fails if file content contains "bug"
        # Note: git bisect checkout might overwrite this file if not untracked/ignored?
        # But here 'test.sh' is untracked, so it stays across checkouts.
        test_script = self.test_dir / "test.sh"
        test_script.write_text("""#!/bin/bash
if grep -q "bug" file.txt; then
  exit 1
else
  exit 0
fi
""")
        test_script.chmod(0o755)

        good_commit = self.commits[1] # v2
        bad_commit = self.commits[3] # v4

        # Run bisect
        # We need absolute path for run command probably, or relative to project root
        success = await run_bisect_logic(
            project_dir=self.test_dir,
            good_commit=good_commit,
            bad_commit=bad_commit,
            run_command=f"./test.sh",
            agent_type="gemini"
        )

        self.assertTrue(success)

        # The bad commit is self.commits[2]
        bad_hash = self.commits[2]

        # Verify agent was called
        self.assertTrue(mock_agent_instance.run_agent_session.called)
        call_args = mock_agent_instance.run_agent_session.call_args[0][0]
        # The prompt should contain the bad hash
        self.assertIn(bad_hash, call_args)
        # And the commit message
        self.assertIn("v3_bug", call_args)

if __name__ == '__main__':
    unittest.main()
