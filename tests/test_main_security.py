import unittest
from unittest.mock import MagicMock, patch
import sys
import argparse
from pathlib import Path
from main import run_security

class TestMainSecurity(unittest.TestCase):

    @patch('main.SecurityAuditor')
    @patch('sys.exit')
    def test_run_security_scan_success(self, mock_exit, MockAuditor):
        # Setup arguments
        args = argparse.Namespace(
            project_dir=Path('.'),
            scan_type='all',
            severity='LOW',
            output='text'
        )

        # Mock Auditor instance
        mock_instance = MockAuditor.return_value
        mock_instance.scan.return_value = [
            {'severity': 'LOW', 'issue_text': 'Minor issue'}
        ]
        mock_instance.format_report.return_value = "Report Content"

        # Run command
        run_security(args)

        # Verify calls
        MockAuditor.assert_called_once()
        mock_instance.scan.assert_called_with(scan_type='all', severity='LOW')
        mock_instance.format_report.assert_called()

        # Should exit with 0 since no HIGH issues
        mock_exit.assert_called_with(0)

    @patch('main.SecurityAuditor')
    @patch('sys.exit')
    def test_run_security_scan_failure(self, mock_exit, MockAuditor):
        # Setup arguments
        args = argparse.Namespace(
            project_dir=Path('.'),
            scan_type='all',
            severity='LOW',
            output='text'
        )

        # Mock Auditor instance with HIGH severity issue
        mock_instance = MockAuditor.return_value
        mock_instance.scan.return_value = [
            {'severity': 'HIGH', 'issue_text': 'Major vulnerability'}
        ]
        # We also need to mock format_report to avoid printing a MagicMock
        mock_instance.format_report.return_value = "High Severity Report"

        # Run command
        run_security(args)

        # Should exit with 1
        mock_exit.assert_called_with(1)

if __name__ == '__main__':
    unittest.main()
