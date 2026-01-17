import unittest
from unittest.mock import MagicMock, patch, mock_open
import sys
from pathlib import Path
import json

# Import the class to be tested
from shared.security import SecurityAuditor

class TestSecurityAuditor(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_run_bandit_installed(self, mock_subprocess, mock_which):
        # Setup mocks
        mock_which.return_value = "/usr/bin/bandit"
        mock_subprocess.return_value.stdout = json.dumps({
            "results": [
                {"test_id": "B101", "issue_text": "Use of assert", "filename": "test.py", "line_number": 1, "issue_severity": "LOW"}
            ]
        })
        mock_subprocess.return_value.returncode = 1 # Bandit exits with 1 on issues

        # Instantiate after patching
        auditor = SecurityAuditor(self.project_dir)

        # Run method
        results = auditor.run_bandit(severity="LOW")

        # Assertions
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["test_id"], "B101")
        mock_subprocess.assert_called_once()
        cmd = mock_subprocess.call_args[0][0]
        self.assertIn("/usr/bin/bandit", cmd)
        self.assertIn("--severity-level", cmd)
        self.assertIn("low", cmd)

    @patch("shutil.which")
    def test_run_bandit_not_installed(self, mock_which):
        mock_which.return_value = None
        # Instantiate after patching
        auditor = SecurityAuditor(self.project_dir)

        results = auditor.run_bandit()
        self.assertEqual(len(results), 1)
        self.assertIn("Bandit is not installed", results[0]["error"])

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_scan_secrets_git(self, mock_subprocess, mock_which):
        mock_which.return_value = "/usr/bin/git"

        # Instantiate after patching
        auditor = SecurityAuditor(self.project_dir)

        # Mock git grep output for AWS Key
        # Format: filename:line:content
        grep_output_akia = "config.py:10:aws_access_key_id='AKIA1234567890123456'\n"
        grep_output_secret = "config.py:11:aws_secret_access_key='secret'\n"

        def subprocess_side_effect(cmd, **kwargs):
            # Check if the pattern in the command matches our mock data
            pattern = cmd[-1]
            if "AKIA" in pattern:
                # Should not have -i
                if "-i" in cmd:
                    return MagicMock(stdout="", returncode=1)
                return MagicMock(stdout=grep_output_akia, returncode=0)
            if "aws_secret_access_key" in pattern:
                # Should have -i
                if "-i" not in cmd:
                    return MagicMock(stdout="", returncode=1)
                return MagicMock(stdout=grep_output_secret, returncode=0)
            return MagicMock(stdout="", returncode=1)

        mock_subprocess.side_effect = subprocess_side_effect

        with patch("pathlib.Path.is_dir", return_value=True):
            findings = auditor.scan_secrets()

        self.assertTrue(len(findings) >= 2)

        # Verify findings
        found_akia = any("AKIA" in f["code"] for f in findings)
        found_secret = any("secret" in f["code"] for f in findings)
        self.assertTrue(found_akia)
        self.assertTrue(found_secret)

    def test_generate_report(self):
        # No external deps, so we can use a fresh instance (assuming bandit check in init doesn't crash)
        # But bandit check in init calls shutil.which. So we should mock it to be safe or just ignore.
        # shutil.which returns None if not found, which is fine.
        auditor = SecurityAuditor(self.project_dir)

        bandit_findings = [
            {"issue_text": "Hardcoded password", "filename": "app.py", "line_number": 5, "issue_severity": "HIGH", "code": "password = '123'"}
        ]
        secret_findings = [
            {"issue_text": "Potential AWS Access Key found", "filename": "config.py", "line_number": 10, "severity": "HIGH", "code": "key = 'AKIA123'"}
        ]

        report = auditor.generate_report(bandit_findings, secret_findings)

        self.assertIn("# 🛡️ Security Audit Report", report)
        self.assertIn("🔴 High Severity: 2", report)
        self.assertIn("Hardcoded password", report)
        self.assertIn("Potential AWS Access Key found", report)
        # Check masking
        self.assertIn("***", report) # Should be masked

if __name__ == '__main__':
    unittest.main()
