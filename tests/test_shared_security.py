import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import json
import sys
import subprocess

from shared.security import SecurityAuditor, SecurityFinding

class TestSecurityAuditor(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.auditor = SecurityAuditor(self.project_dir)

    @patch("shutil.which")
    def test_run_bandit_not_installed(self, mock_which):
        mock_which.return_value = None
        result = self.auditor.run_bandit()
        self.assertIn("error", result)
        self.assertIn("Bandit is not installed", result["error"])

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_run_bandit_success(self, mock_run, mock_which):
        mock_which.return_value = "/usr/bin/bandit"

        mock_output = {
            "results": [
                {
                    "test_id": "B101",
                    "issue_text": "Use of assert detected.",
                    "issue_severity": "LOW",
                    "issue_confidence": "HIGH",
                    "filename": "test.py",
                    "line_number": 10,
                    "more_info": "http://link"
                }
            ],
            "metrics": {"_totals": {"loc": 100}}
        }

        mock_run.return_value = MagicMock(
            stdout=json.dumps(mock_output),
            returncode=1 # Bandit returns 1 on issues
        )

        result = self.auditor.run_bandit()
        self.assertEqual(result, mock_output)

        # Verify args
        args = mock_run.call_args[0][0]
        self.assertIn("--severity-level", args)
        self.assertIn("medium", args) # Default

    @patch("pathlib.Path.read_text")
    @patch("os.walk")
    def test_check_secrets(self, mock_walk, mock_read_text):
        # Mock file system structure
        mock_walk.return_value = [
            (str(self.project_dir), [], ["config.py", "safe.py"])
        ]

        # Mock file content
        def read_side_effect(errors=None):
            # We can't easily know which file is being read here because
            # Path.read_text is called on a new Path instance created inside the loop.
            # So we will mock os.walk to return specific file paths, and we'll assume
            # the order or just return content based on call count?
            # Better strategy: Mock Path.read_text on the instance? No, they are new instances.
            # Let's just return a secret for one call and safe for another.
            pass

        # Actually, simpler to just mock read_text to return a secret
        mock_read_text.return_value = "aws_key = 'AKIAIOSFODNN7EXAMPLE'"

        # We need to make sure the file path check passes
        with patch("pathlib.Path.stat") as mock_stat:
            mock_stat.return_value.st_size = 100
            findings = self.auditor.check_secrets()

        self.assertEqual(len(findings), 2) # Both files have the secret
        self.assertEqual(findings[0]['type'], "AWS Access Key")

    def test_generate_report(self):
        bandit_results = {
            "results": [
                {
                    "test_id": "B101",
                    "issue_text": "Assert used",
                    "issue_severity": "LOW",
                    "issue_confidence": "HIGH",
                    "filename": "test.py",
                    "line_number": 1,
                    "more_info": "link"
                }
            ],
            "metrics": {"total": 1}
        }
        secret_findings = [
            {"type": "AWS Key", "file": "config.py", "severity": "HIGH"}
        ]

        report = self.auditor.generate_report(bandit_results, secret_findings)

        self.assertIn("Security Audit Report", report)
        self.assertIn("Static Analysis (Bandit)", report)
        self.assertIn("Assert used", report)
        self.assertIn("Secret Scanning", report)
        self.assertIn("AWS Key", report)

if __name__ == '__main__':
    unittest.main()
