import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys
import os

# Add repo root to sys.path to import main
sys.path.append(str(Path(__file__).parent.parent))

from main import run_security

class TestMainSecurity(unittest.TestCase):

    @patch("main.SecurityAuditor")
    @patch("main.shutil.which")
    def test_run_security_all_checks(self, mock_which, mock_auditor_class):
        # Setup mocks
        mock_auditor = mock_auditor_class.return_value
        mock_auditor.findings = []
        mock_auditor.generate_report.return_value = "Report"
        mock_which.return_value = "/usr/bin/bandit" # Simulate bandit installed

        # Setup args
        args = MagicMock()
        args.project_dir = Path(".")
        args.scan_type = "all"
        args.severity = "LOW"
        args.output = None

        # Run function
        with self.assertRaises(SystemExit) as cm:
            run_security(args)

        self.assertEqual(cm.exception.code, 0)

        # Verify calls
        mock_auditor.run_bandit_scan.assert_called_once_with(severity="low")
        mock_auditor.scan_secrets.assert_called_once()
        mock_auditor.generate_report.assert_called_once()

    @patch("main.SecurityAuditor")
    @patch("main.shutil.which")
    def test_run_security_fail_on_high_severity(self, mock_which, mock_auditor_class):
        # Setup mocks
        mock_auditor = mock_auditor_class.return_value
        mock_auditor.findings = [{"severity": "HIGH", "message": "Bad!"}]
        mock_auditor.generate_report.return_value = "Report"
        mock_which.return_value = "/usr/bin/bandit"

        # Setup args
        args = MagicMock()
        args.project_dir = Path(".")
        args.scan_type = "bandit"
        args.severity = "LOW"
        args.output = None

        # Run function
        with self.assertRaises(SystemExit) as cm:
            run_security(args)

        self.assertEqual(cm.exception.code, 1)

    @patch("main.SecurityAuditor")
    def test_run_security_save_output(self, mock_auditor_class):
        mock_auditor = mock_auditor_class.return_value
        mock_auditor.findings = []
        mock_auditor.generate_report.return_value = "Report Content"

        mock_output = MagicMock()

        args = MagicMock()
        args.project_dir = Path(".")
        args.scan_type = "secrets"
        args.output = mock_output

        with self.assertRaises(SystemExit) as cm:
            run_security(args)

        self.assertEqual(cm.exception.code, 0)
        mock_output.write_text.assert_called_once_with("Report Content")

if __name__ == "__main__":
    unittest.main()
