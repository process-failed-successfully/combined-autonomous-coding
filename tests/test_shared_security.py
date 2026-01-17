import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import json
import shutil
from shared.security import SecurityAuditor

class TestSecurityAuditor(unittest.TestCase):

    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.auditor = SecurityAuditor(self.project_dir)

    @patch('shutil.which')
    def test_run_bandit_missing(self, mock_which):
        mock_which.return_value = None
        # Need to re-init to pick up the mock
        auditor = SecurityAuditor(self.project_dir)
        findings = auditor.run_bandit()
        self.assertEqual(findings, [])

    @patch('subprocess.run')
    @patch('shutil.which')
    def test_run_bandit_success(self, mock_which, mock_run):
        mock_which.return_value = '/usr/bin/bandit'
        auditor = SecurityAuditor(self.project_dir)

        mock_result = MagicMock()
        mock_result.returncode = 1 # Bandit exits with 1 on issues
        mock_result.stdout = json.dumps({
            "results": [
                {"issue_severity": "HIGH", "issue_text": "Hardcoded password"}
            ]
        })
        mock_run.return_value = mock_result

        findings = auditor.run_bandit(severity='HIGH')

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['issue_text'], "Hardcoded password")

        # Verify args
        args, kwargs = mock_run.call_args
        cmd = args[0]
        self.assertIn('-lll', cmd) # High severity
        self.assertIn('/usr/bin/bandit', cmd)

    @patch('os.walk')
    @patch('builtins.open')
    def test_scan_secrets(self, mock_open, mock_walk):
        mock_walk.return_value = [
            (str(self.project_dir), [], ['config.py'])
        ]

        # Mock file content
        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = "aws_secret_access_key = 'AKIA1234567890123456'"
        mock_open.return_value = mock_file

        findings = self.auditor.scan_secrets()

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['type'], 'secret')
        self.assertIn('AWS Access Key ID', findings[0]['issue_text'])

    def test_format_report(self):
        findings = [
            {'severity': 'HIGH', 'issue_text': 'Bad thing', 'filename': 'file.py', 'line_number': 10},
            {'severity': 'LOW', 'issue_text': 'Minor thing', 'filename': 'file.py', 'line_number': 20}
        ]

        report = self.auditor.format_report(findings, output_format='text')
        self.assertIn("Found 2 security issue(s)", report)
        self.assertIn("🔴 HIGH - Bad thing", report)
        self.assertIn("🔵 LOW - Minor thing", report)

        json_report = self.auditor.format_report(findings, output_format='json')
        data = json.loads(json_report)
        self.assertEqual(len(data), 2)

if __name__ == '__main__':
    unittest.main()
