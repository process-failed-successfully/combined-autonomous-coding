import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import tempfile
import shutil
import os
from shared.security import SecurityAuditor

class TestSecurityAuditor(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.auditor = SecurityAuditor(self.project_dir)

    @patch("shared.security.subprocess.run")
    def test_run_bandit_scan_success(self, mock_run):
        # Mock bandit output
        mock_output = """
        {
            "results": [
                {
                    "test_id": "B101",
                    "issue_text": "Use of assert detected.",
                    "filename": "test.py",
                    "line_number": 10,
                    "issue_severity": "LOW",
                    "issue_confidence": "HIGH"
                }
            ]
        }
        """
        mock_run.return_value = MagicMock(stdout=mock_output, returncode=1)

        findings = self.auditor.run_bandit_scan()

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["type"], "Static Analysis (Bandit)")
        self.assertEqual(findings[0]["check_id"], "B101")
        self.assertEqual(findings[0]["severity"], "LOW")

    @patch("shared.security.subprocess.run")
    def test_run_bandit_not_found(self, mock_run):
        mock_run.side_effect = FileNotFoundError

        findings = self.auditor.run_bandit_scan()

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["type"], "System Error")
        self.assertEqual(findings[0]["severity"], "CRITICAL")

    def test_scan_secrets_real_file(self):
        # Create a temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a file with a fake secret
            secret_file = temp_path / "config.py"
            secret_file.write_text("AWS_ACCESS_KEY_ID = 'AKIA1234567890123456'")

            # Create a safe file
            safe_file = temp_path / "safe.py"
            safe_file.write_text("print('hello world')")

            # Initialize auditor with temp path
            auditor = SecurityAuditor(temp_path)

            # Run scan
            findings = auditor.scan_secrets()

            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0]["type"], "Secret Detection")
            self.assertIn("Potential AWS Access Key ID found", findings[0]["message"])
            self.assertEqual(findings[0]["file"], "config.py")

    def test_generate_report(self):
        self.auditor.findings = [
            {
                "type": "Test Issue",
                "message": "Something wrong",
                "file": "test.py",
                "line": 1,
                "severity": "HIGH",
                "confidence": "MEDIUM"
            }
        ]

        report = self.auditor.generate_report()
        self.assertIn("🛡️ Security Audit Report", report)
        self.assertIn("Total Issues: 1", report)
        self.assertIn("🔴 [HIGH] Test Issue", report)
        self.assertIn("Confidence: MEDIUM", report)

if __name__ == "__main__":
    unittest.main()
