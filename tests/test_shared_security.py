import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import json
from shared.security import SecurityAuditor
import tempfile
import shutil
import os

class TestSecurityAuditor(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        self.auditor = SecurityAuditor(self.project_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('subprocess.run')
    def test_run_bandit_success(self, mock_run):
        # Mock bandit output
        mock_output = {
            "results": [
                {
                    "issue_severity": "HIGH",
                    "filename": "vuln.py",
                    "line_number": 10,
                    "issue_text": "Possible hardcoded password",
                    "code": "password = '123'",
                    "more_info": "https://bandit.readthedocs.io/"
                }
            ]
        }
        mock_run.return_value = MagicMock(stdout=json.dumps(mock_output), stderr="", returncode=0)

        findings = self.auditor.run_bandit()

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['tool'], 'bandit')
        self.assertEqual(findings[0]['severity'], 'HIGH')
        self.assertEqual(findings[0]['file'], 'vuln.py')

    @patch('subprocess.run')
    def test_run_bandit_failure(self, mock_run):
        # Mock bandit not found or crashing
        mock_run.side_effect = FileNotFoundError

        findings = self.auditor.run_bandit()

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['type'], 'error')
        self.assertIn("Bandit executable not found", findings[0]['message'])

    def test_scan_secrets(self):
        # Create a file with a fake secret
        secret_file = self.project_dir / "config.py"
        secret_file.write_text("aws_key = 'AKIAIOSFODNN7EXAMPLE'", encoding='utf-8')

        # Create a safe file
        safe_file = self.project_dir / "utils.py"
        safe_file.write_text("print('hello')", encoding='utf-8')

        findings = self.auditor.scan_secrets()

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['tool'], 'secret-scanner')
        self.assertEqual(findings[0]['severity'], 'HIGH')
        self.assertIn("config.py", findings[0]['file'])
        self.assertIn("AWS Access Key", findings[0]['message'])

    def test_scan_secrets_ignores(self):
        # Create a secret in an ignored directory
        ignored_dir = self.project_dir / ".git"
        ignored_dir.mkdir()
        secret_file = ignored_dir / "config"
        secret_file.write_text("aws_key = 'AKIAIOSFODNN7EXAMPLE'", encoding='utf-8')

        findings = self.auditor.scan_secrets()
        self.assertEqual(len(findings), 0)

    def test_generate_report(self):
        self.auditor.findings = [
            {'tool': 'bandit', 'severity': 'HIGH', 'message': 'Issue 1', 'file': 'a.py', 'line': 1},
            {'tool': 'secret-scanner', 'severity': 'HIGH', 'message': 'Secret 1', 'file': 'b.py', 'line': 2}
        ]

        report = self.auditor.generate_report()

        self.assertIn("⚠️ Security Audit Report", report)
        self.assertIn("🔴 [HIGH] bandit: Issue 1", report)
        self.assertIn("🔴 [HIGH] secret-scanner: Secret 1", report)
        self.assertIn("High: 2", report)

if __name__ == '__main__':
    unittest.main()
