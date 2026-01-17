import unittest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
import json
import sys
import os

# Adjust path to import shared
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.security import SecurityAuditor

class TestSecurityAuditor(unittest.TestCase):

    def setUp(self):
        self.project_dir = Path("/tmp/project")
        self.auditor = SecurityAuditor(self.project_dir)

    def test_mask_secret(self):
        self.assertEqual(self.auditor._mask_secret("123"), "***")
        self.assertEqual(self.auditor._mask_secret("12345678"), "********")
        self.assertEqual(self.auditor._mask_secret("1234567890"), "1234**7890")
        self.assertEqual(self.auditor._mask_secret("AKIAIOSFODNN7EXAMPLE"), "AKIA************MPLE")

    @patch("shared.security.shutil.which")
    @patch("shared.security.os.walk")
    @patch("builtins.open", new_callable=mock_open)
    def test_scan_secrets_found(self, mock_file, mock_walk, mock_which):
        mock_which.return_value = None # No git
        mock_walk.return_value = [
            (str(self.project_dir), [], ["config.py"])
        ]

        # Mock file content with a secret
        secret_content = "aws_access_key_id = 'AKIAIOSFODNN7EXAMPLE'"
        mock_file.return_value.read.return_value = secret_content

        findings = self.auditor.scan_secrets()

        self.assertEqual(len(findings), 1)
        finding = findings[0]
        self.assertEqual(finding['check_id'], "AWS_ACCESS_KEY")
        self.assertEqual(finding['severity'], "HIGH")
        self.assertIn("AKIA************MPLE", finding['code'])

    @patch("shared.security.shutil.which")
    @patch("shared.security.subprocess.run")
    def test_run_bandit_success(self, mock_run, mock_which):
        mock_which.return_value = "/usr/bin/bandit"

        bandit_output = {
            "results": [
                {
                    "test_id": "B101",
                    "filename": "/tmp/project/app.py",
                    "line_number": 10,
                    "issue_severity": "MEDIUM",
                    "issue_text": "Use of assert detected.",
                    "code": "assert True"
                }
            ]
        }

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(bandit_output)
        )

        findings = self.auditor.run_bandit()

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['check_id'], "B101")
        self.assertEqual(findings[0]['severity'], "MEDIUM")

        # Verify args
        args, kwargs = mock_run.call_args
        cmd = args[0]
        self.assertIn("--severity-level", cmd)
        self.assertIn("low", cmd)
        self.assertIn("-f", cmd)
        self.assertIn("json", cmd)

    @patch("shared.security.shutil.which")
    def test_run_bandit_not_found(self, mock_which):
        mock_which.return_value = None
        findings = self.auditor.run_bandit()
        self.assertEqual(findings, [])

    def test_generate_report(self):
        findings = [
            {
                "type": "secret",
                "check_id": "AWS_KEY",
                "path": "config.py",
                "line": 1,
                "severity": "HIGH",
                "message": "Found key",
                "code": "***"
            },
            {
                "type": "sast",
                "check_id": "B101",
                "path": "app.py",
                "line": 10,
                "severity": "LOW",
                "message": "Assert used",
                "code": "assert"
            }
        ]

        report = self.auditor.generate_report(findings)

        self.assertIn("# Security Audit Report", report)
        self.assertIn("Found 2 issues", report)
        # Check sorting (High before Low)
        high_idx = report.find("HIGH")
        low_idx = report.find("LOW")
        self.assertLess(high_idx, low_idx)

if __name__ == '__main__':
    unittest.main()
