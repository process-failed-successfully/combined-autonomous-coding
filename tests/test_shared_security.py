import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import shutil
import json
from shared.security import SecurityAuditor

class TestSecurityAuditor(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        self.auditor = SecurityAuditor(self.project_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('shared.security.shutil.which')
    @patch('shared.security.subprocess.run')
    def test_run_bandit_success(self, mock_run, mock_which):
        mock_which.return_value = "/usr/bin/bandit"

        bandit_output = {
            "results": [
                {
                    "test_id": "B101",
                    "issue_text": "Use of assert detected.",
                    "filename": "test.py",
                    "line_number": 10,
                    "issue_severity": "LOW",
                    "issue_confidence": "HIGH",
                    "code": "assert True"
                }
            ]
        }

        mock_run.return_value = MagicMock(
            returncode=1, # Bandit returns 1 on findings
            stdout=json.dumps(bandit_output),
            stderr=""
        )

        findings = self.auditor.run_bandit()

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['check_id'], 'B101')
        self.assertEqual(len(self.auditor.findings), 1)

        # Verify subprocess call
        args = mock_run.call_args[0][0]
        self.assertIn("-f", args)
        self.assertIn("json", args)

    @patch('shared.security.shutil.which')
    def test_run_bandit_not_found(self, mock_which):
        mock_which.return_value = None
        findings = self.auditor.run_bandit()
        self.assertEqual(len(findings), 0)

    def test_scan_secrets(self):
        # Create a file with a fake secret
        secret_file = self.project_dir / "config.py"
        # Matches Generic API Key: "api_key" ... '...' (16-64 chars)
        fake_key = "my_api_key = '12345678901234567890123456789012'"
        secret_file.write_text(fake_key)

        findings = self.auditor.scan_secrets()

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['check_id'], 'SECRET_REGEX')
        self.assertIn("Generic API Key", findings[0]['description'])

    def test_generate_report_empty(self):
        report = self.auditor.generate_report()
        self.assertIn("No security issues found", report)

    def test_generate_report_with_findings(self):
        self.auditor.findings = [
            {
                "type": "Static Analysis (Bandit)",
                "check_id": "B101",
                "description": "Issue Description",
                "file": "test.py",
                "line": 1,
                "severity": "LOW",
                "confidence": "HIGH",
                "code": "code"
            }
        ]

        report = self.auditor.generate_report()
        self.assertIn("Security Audit Report", report)
        self.assertIn("Static Analysis (1)", report)
        self.assertIn("Issue Description", report)

if __name__ == "__main__":
    unittest.main()
