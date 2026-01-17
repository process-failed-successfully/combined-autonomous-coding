
import unittest
from unittest.mock import MagicMock, patch
import argparse
from pathlib import Path
import sys
import main

class TestMainSecurity(unittest.TestCase):

    @patch("main.SecurityAuditor")
    def test_run_security_command(self, MockAuditor):
        """Test the security command execution flow."""
        # Setup mock
        mock_auditor_instance = MockAuditor.return_value
        mock_auditor_instance.run_security_scan.return_value = {
            "findings": [
                {"severity": "HIGH", "issue_text": "Test Issue", "filename": "test.py", "line_number": 1}
            ],
            "summary": {"total": 1, "high": 1, "medium": 0, "low": 0}
        }

        # Setup args
        args = argparse.Namespace(
            command="security",
            project_dir=Path("."),
            scan_type="all",
            severity="LOW",
            output=None
        )

        # We expect sys.exit(1) because HIGH severity issues are found
        with self.assertRaises(SystemExit) as cm:
            main.run_security(args)

        self.assertEqual(cm.exception.code, 1)

        # Verify auditor was called correctly
        mock_auditor_instance.run_security_scan.assert_called_once_with(
            project_dir=Path(".").resolve(),
            scan_type="all",
            severity="LOW"
        )

    @patch("main.SecurityAuditor")
    def test_run_security_clean(self, MockAuditor):
        """Test the security command with no issues."""
        # Setup mock
        mock_auditor_instance = MockAuditor.return_value
        mock_auditor_instance.run_security_scan.return_value = {
            "findings": [],
            "summary": {"total": 0, "high": 0, "medium": 0, "low": 0}
        }

        # Setup args
        args = argparse.Namespace(
            command="security",
            project_dir=Path("."),
            scan_type="all",
            severity="LOW",
            output=None
        )

        # Expect sys.exit(0)
        with self.assertRaises(SystemExit) as cm:
            main.run_security(args)

        self.assertEqual(cm.exception.code, 0)

if __name__ == "__main__":
    unittest.main()
