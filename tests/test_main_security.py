import unittest
from unittest.mock import patch, MagicMock
import sys
from io import StringIO
import argparse
from pathlib import Path

# Need to make sure we can import main
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import run_security

class TestMainSecurity(unittest.TestCase):

    @patch('main.SecurityAuditor')
    def test_run_security_audit_all(self, MockAuditor):
        # Setup mock
        mock_auditor = MockAuditor.return_value
        mock_auditor.run_bandit.return_value = [{'severity': 'LOW'}]
        mock_auditor.scan_secrets.return_value = [{'severity': 'HIGH'}]
        mock_auditor.generate_report.return_value = "Report Content"
        mock_auditor.findings = [{'severity': 'LOW'}, {'severity': 'HIGH'}]

        args = argparse.Namespace(
            project_dir=Path('.'),
            scan_secrets=False,
            scan_code=False,
            severity='medium',
            output=None,
            fail_on_high=False
        )

        # Capture stdout
        captured_output = StringIO()
        sys.stdout = captured_output

        try:
            with self.assertRaises(SystemExit) as cm:
                run_security(args)
            self.assertEqual(cm.exception.code, 0)
        finally:
            sys.stdout = sys.__stdout__

        # Verification
        mock_auditor.run_bandit.assert_called_once()
        mock_auditor.scan_secrets.assert_called_once()
        self.assertIn("Report Content", captured_output.getvalue())

    @patch('main.SecurityAuditor')
    def test_run_security_scan_secrets_only(self, MockAuditor):
        mock_auditor = MockAuditor.return_value
        mock_auditor.scan_secrets.return_value = []
        mock_auditor.generate_report.return_value = ""

        args = argparse.Namespace(
            project_dir=Path('.'),
            scan_secrets=True, # ONLY secrets
            scan_code=False,
            severity='medium',
            output=None,
            fail_on_high=False
        )

        captured_output = StringIO()
        sys.stdout = captured_output
        try:
            with self.assertRaises(SystemExit):
                run_security(args)
        finally:
            sys.stdout = sys.__stdout__

        mock_auditor.run_bandit.assert_not_called()
        mock_auditor.scan_secrets.assert_called_once()

    @patch('main.SecurityAuditor')
    def test_run_security_fail_on_high(self, MockAuditor):
        mock_auditor = MockAuditor.return_value
        mock_auditor.findings = [{'severity': 'HIGH'}] # Simulate finding a high severity issue

        args = argparse.Namespace(
            project_dir=Path('.'),
            scan_secrets=False,
            scan_code=False,
            severity='medium',
            output=None,
            fail_on_high=True # Should trigger failure
        )

        captured_output = StringIO()
        sys.stdout = captured_output
        captured_stderr = StringIO()
        sys.stderr = captured_stderr

        try:
            with self.assertRaises(SystemExit) as cm:
                run_security(args)
            self.assertEqual(cm.exception.code, 1)
        finally:
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__

        self.assertIn("FAILED: Found 1 HIGH severity issue(s)", captured_stderr.getvalue())

if __name__ == '__main__':
    unittest.main()
