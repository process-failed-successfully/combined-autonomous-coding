import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import os

# Ensure main.py can be imported
sys.path.append(str(Path(__file__).parent.parent))

# Import run_security from main
from main import run_security

class TestMainSecurity(unittest.TestCase):
    @patch('shared.security.SecurityAuditor')
    def test_run_security_basic(self, MockAuditor):
        # Setup mock
        mock_instance = MockAuditor.return_value
        mock_instance.findings = []
        mock_instance.generate_report.return_value = "Report"

        # Setup args
        args = MagicMock()
        args.project_dir = Path(".")
        args.scan_type = "all"
        args.severity = "medium"
        args.confidence = "medium"
        args.output = None
        args.no_fail = False

        # Run
        with self.assertRaises(SystemExit) as cm:
            run_security(args)

        self.assertEqual(cm.exception.code, 0)

        # Verify calls
        mock_instance.run_bandit.assert_called_once()
        mock_instance.scan_secrets.assert_called_once()

    @patch('shared.security.SecurityAuditor')
    def test_run_security_fail_on_high_severity(self, MockAuditor):
        # Setup mock with high severity finding
        mock_instance = MockAuditor.return_value
        mock_instance.findings = [{'severity': 'HIGH'}]
        mock_instance.generate_report.return_value = "Report"

        args = MagicMock()
        args.project_dir = Path(".")
        args.scan_type = "all"
        args.severity = "medium"
        args.confidence = "medium"
        args.output = None
        args.no_fail = False # Default behavior

        with self.assertRaises(SystemExit) as cm:
            run_security(args)

        self.assertEqual(cm.exception.code, 1)

    @patch('shared.security.SecurityAuditor')
    def test_run_security_no_fail_flag(self, MockAuditor):
        # Setup mock with high severity finding
        mock_instance = MockAuditor.return_value
        mock_instance.findings = [{'severity': 'HIGH'}]
        mock_instance.generate_report.return_value = "Report"

        args = MagicMock()
        args.project_dir = Path(".")
        args.scan_type = "all"
        args.severity = "medium"
        args.confidence = "medium"
        args.output = None
        args.no_fail = True # Flag set

        with self.assertRaises(SystemExit) as cm:
            run_security(args)

        self.assertEqual(cm.exception.code, 0)

if __name__ == "__main__":
    unittest.main()
