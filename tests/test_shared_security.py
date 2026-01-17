import unittest
import tempfile
import shutil
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from shared.security import SecurityAuditor

class TestSecurityAuditor(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        self.auditor = SecurityAuditor(self.project_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_scan_secrets_finds_aws_key(self):
        """Test that scan_secrets detects AWS keys."""
        secret_file = self.project_dir / "secret.py"
        # Create a file with a fake AWS key
        # AKIA + 16 chars
        fake_key = "AKIAABCDEFGHIJKLMNOP"
        with open(secret_file, "w") as f:
            f.write(f"key = '{fake_key}'\n")

        findings = self.auditor.scan_secrets()

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['type'], "AWS Access Key")
        self.assertIn("secret.py", findings[0]['file'])
        # Check masking
        self.assertNotIn(fake_key, findings[0]['snippet'])
        self.assertIn("AKIA********", findings[0]['snippet'])

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_run_bandit_success(self, mock_which, mock_run):
        """Test run_bandit handles success output."""
        mock_which.return_value = "/usr/bin/bandit"

        # Mock bandit JSON output
        bandit_output = {
            "results": [
                {
                    "test_id": "B101",
                    "issue_text": "Use of assert detected.",
                    "filename": "test.py",
                    "line_number": 1,
                    "issue_severity": "LOW",
                    "more_info": "link"
                }
            ]
        }

        mock_run.return_value = MagicMock(
            stdout=json.dumps(bandit_output),
            stderr="",
            returncode=1 # Bandit returns 1 on issues
        )

        results = self.auditor.run_bandit()

        self.assertIn("results", results)
        self.assertEqual(len(results["results"]), 1)
        self.assertEqual(results["results"][0]["test_id"], "B101")

    @patch("shutil.which")
    def test_run_bandit_not_installed(self, mock_which):
        """Test run_bandit handles missing bandit executable."""
        mock_which.return_value = None

        results = self.auditor.run_bandit()
        self.assertIn("error", results)
        self.assertIn("not installed", results["error"])

if __name__ == "__main__":
    unittest.main()
