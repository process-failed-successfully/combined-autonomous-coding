import unittest
from unittest.mock import MagicMock, patch
import sys
import argparse
from pathlib import Path

# Import the function to test
# Assuming main.py is in the python path or we can import it
import main

class TestMainSecurity(unittest.TestCase):

    # We patch the module where SecurityAuditor is imported from, which is inside run_security.
    # But since it's imported locally, we have to mock it differently or move the import.
    # The patch target needs to be where the class is looked up.
    # Since run_security does `from shared.security import SecurityAuditor`,
    # we should patch `shared.security.SecurityAuditor`.

    @patch("shared.security.SecurityAuditor")
    @patch("sys.exit")
    def test_run_security_clean(self, mock_exit, MockAuditor):
        # Setup mock
        auditor_instance = MockAuditor.return_value
        auditor_instance.run_bandit.return_value = {"results": []}
        auditor_instance.check_secrets.return_value = []
        auditor_instance.generate_report.return_value = "Clean Report"

        args = argparse.Namespace(
            project_dir=Path("/tmp/test"),
            severity="MEDIUM",
            confidence="MEDIUM",
            no_secrets=False,
            output=None
        )

        # Run
        main.run_security(args)

        # Verify
        auditor_instance.run_bandit.assert_called_with(severity="MEDIUM", confidence="MEDIUM")
        auditor_instance.check_secrets.assert_called_once()
        mock_exit.assert_called_with(0)

    @patch("shared.security.SecurityAuditor")
    @patch("sys.exit")
    def test_run_security_issues(self, mock_exit, MockAuditor):
        # Setup mock
        auditor_instance = MockAuditor.return_value
        auditor_instance.run_bandit.return_value = {
            "results": [{"issue_severity": "HIGH", "issue_text": "Bad"}]
        }
        auditor_instance.check_secrets.return_value = []
        auditor_instance.generate_report.return_value = "Bad Report"

        args = argparse.Namespace(
            project_dir=Path("/tmp/test"),
            severity="MEDIUM",
            confidence="MEDIUM",
            no_secrets=False,
            output=None
        )

        # Run
        main.run_security(args)

        # Verify
        mock_exit.assert_called_with(1)

    @patch("shared.security.SecurityAuditor")
    @patch("sys.exit")
    def test_run_security_secrets(self, mock_exit, MockAuditor):
        # Setup mock
        auditor_instance = MockAuditor.return_value
        auditor_instance.run_bandit.return_value = {"results": []}
        auditor_instance.check_secrets.return_value = [{"type": "Secret"}]
        auditor_instance.generate_report.return_value = "Secret Report"

        args = argparse.Namespace(
            project_dir=Path("/tmp/test"),
            severity="MEDIUM",
            confidence="MEDIUM",
            no_secrets=False,
            output=None
        )

        # Run
        main.run_security(args)

        # Verify
        mock_exit.assert_called_with(1)

if __name__ == '__main__':
    unittest.main()
