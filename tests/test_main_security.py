import unittest
from unittest.mock import MagicMock, patch
import sys
import main
from pathlib import Path

class TestMainSecurity(unittest.TestCase):

    @patch("main.SecurityAuditor")
    def test_run_security_defaults(self, mock_auditor_cls):
        # Setup mock
        mock_auditor = mock_auditor_cls.return_value
        mock_auditor.run_all.return_value = []

        # Setup args
        args = MagicMock()
        args.project_dir = Path(".")
        args.scan_type = "all"
        args.severity = "low"
        args.output = None

        # Run command (should exit 0)
        with self.assertRaises(SystemExit) as cm:
            main.run_security(args)
        self.assertEqual(cm.exception.code, 0)

        # Verify calls
        mock_auditor_cls.assert_called_with(Path(".").resolve())
        mock_auditor.run_all.assert_called_with(scan_type="all", severity="low")

    @patch("main.SecurityAuditor")
    def test_run_security_with_findings(self, mock_auditor_cls):
        # Setup mock
        mock_auditor = mock_auditor_cls.return_value
        mock_auditor.run_all.return_value = [
            {
                "type": "secret",
                "severity": "HIGH",
                "description": "AWS Key found",
                "file": "config.py",
                "line": 1
            }
        ]

        # Setup args
        args = MagicMock()
        args.project_dir = Path(".")
        args.scan_type = "all"
        args.severity = "low"
        args.output = None

        # Run command (should exit 1 because of HIGH severity)
        with self.assertRaises(SystemExit) as cm:
            main.run_security(args)
        self.assertEqual(cm.exception.code, 1)

    @patch("main.SecurityAuditor")
    def test_run_security_output_file(self, mock_auditor_cls):
        # Setup mock
        mock_auditor = mock_auditor_cls.return_value
        mock_auditor.run_all.return_value = []

        # Setup args
        output_file = Path("security_report.json")
        args = MagicMock()
        args.project_dir = Path(".")
        args.scan_type = "sast"
        args.severity = "medium"
        args.output = str(output_file)

        # Run command
        with self.assertRaises(SystemExit) as cm:
            main.run_security(args)
        self.assertEqual(cm.exception.code, 0)

        # Verify output file creation
        self.assertTrue(output_file.exists())
        output_file.unlink() # Cleanup

if __name__ == "__main__":
    unittest.main()
