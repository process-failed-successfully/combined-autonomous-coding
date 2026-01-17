import unittest
from unittest.mock import patch, MagicMock
from argparse import Namespace
from pathlib import Path
from main import run_security

class TestMainSecurity(unittest.TestCase):

    @patch("shared.security.SecurityAuditor")
    @patch("sys.exit")
    def test_run_security_no_issues(self, mock_exit, MockAuditor):
        # Setup
        args = Namespace(
            project_dir=Path("."),
            scan_type="all",
            severity="LOW",
            output=None
        )

        mock_instance = MockAuditor.return_value
        mock_instance.run_all.return_value = []

        # Execute
        run_security(args)

        # Assert
        mock_instance.run_all.assert_called_once_with("LOW")
        mock_exit.assert_called_once_with(0)

    @patch("shared.security.SecurityAuditor")
    @patch("sys.exit")
    def test_run_security_with_issues(self, mock_exit, MockAuditor):
        # Setup
        args = Namespace(
            project_dir=Path("."),
            scan_type="bandit",
            severity="MEDIUM",
            output=None
        )

        mock_instance = MockAuditor.return_value
        mock_instance.run_bandit.return_value = [
            {"tool": "bandit", "severity": "HIGH", "message": "Bad code", "file": "app.py", "line": 1}
        ]

        # Execute
        run_security(args)

        # Assert
        mock_instance.run_bandit.assert_called_once_with("MEDIUM")
        mock_exit.assert_called_once_with(1) # Exit 1 due to HIGH severity

    @patch("shared.security.SecurityAuditor")
    @patch("sys.exit")
    @patch("main.json.dump")
    @patch("builtins.open")
    def test_run_security_output_file(self, mock_open, mock_json_dump, mock_exit, MockAuditor):
        # Setup
        args = Namespace(
            project_dir=Path("."),
            scan_type="secrets",
            severity="LOW",
            output=Path("report.json")
        )

        mock_instance = MockAuditor.return_value
        mock_instance.scan_secrets.return_value = [
            {"tool": "secret-scanner", "severity": "MEDIUM", "message": "Secret", "file": "config.py", "line": 1}
        ]

        # Execute
        run_security(args)

        # Assert
        mock_instance.scan_secrets.assert_called_once()
        mock_open.assert_called_once()
        mock_json_dump.assert_called_once()
        mock_exit.assert_called_once_with(0) # No HIGH severity

if __name__ == "__main__":
    unittest.main()
