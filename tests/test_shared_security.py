import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.security import SecurityAuditor

class TestSecurityAuditor(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.auditor = SecurityAuditor(self.project_dir)

    @patch("shutil.which")
    @patch("asyncio.create_subprocess_exec")
    async def test_run_bandit_success(self, mock_exec, mock_which):
        mock_which.return_value = "/usr/bin/bandit"

        # Mock subprocess
        process = AsyncMock()
        process.communicate.return_value = (
            b'{"results": [{"issue_text": "Weak crypto"}]}',
            b""
        )
        mock_exec.return_value = process

        await self.auditor.run_bandit()

        self.assertIn("results", self.auditor.results["bandit"])
        self.assertEqual(len(self.auditor.results["bandit"]["results"]), 1)
        self.assertEqual(self.auditor.results["bandit"]["results"][0]["issue_text"], "Weak crypto")

    @patch("shutil.which")
    async def test_run_bandit_not_installed(self, mock_which):
        mock_which.return_value = None
        await self.auditor.run_bandit()
        self.assertIn("error", self.auditor.results["bandit"])
        self.assertIn("not installed", self.auditor.results["bandit"]["error"])

    @patch("subprocess.run")
    @patch("shutil.which")
    @patch("pathlib.Path.is_dir") # Mock is_dir to return True for .git check
    def test_scan_secrets_git(self, mock_is_dir, mock_which, mock_run):
        mock_which.return_value = "/usr/bin/git"
        mock_is_dir.return_value = True # Simulate .git directory exists

        # Mock git grep output
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "src/config.py:10:AWS_KEY='AKIA...'"

        self.auditor.scan_secrets()

        self.assertTrue(any("AWS Access Key" in s for s in self.auditor.results["secrets"]))

    def test_summary_generation(self):
        self.auditor.results["bandit"] = {
            "results": [
                {"issue_severity": "HIGH"},
                {"issue_severity": "MEDIUM"}
            ]
        }
        self.auditor.results["secrets"] = ["Found secret 1", "Found secret 2"]

        self.auditor._generate_summary()

        summary = self.auditor.results["summary"]
        self.assertEqual(summary["total_issues"], 4)
        self.assertEqual(summary["high_severity"], 1)
        self.assertEqual(summary["medium_severity"], 1)
        self.assertEqual(summary["secrets_found"], 2)

if __name__ == "__main__":
    unittest.main()
