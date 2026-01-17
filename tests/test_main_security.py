import unittest
from unittest.mock import MagicMock, patch
import sys
import os
from pathlib import Path
import argparse

# Adjust path to import main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import run_security

class TestMainSecurity(unittest.TestCase):

    def setUp(self):
        self.args = argparse.Namespace(
            project_dir=Path("."),
            scan_type="all",
            severity="LOW",
            output=None
        )

    @patch("shared.security.SecurityAuditor")
    def test_run_security_no_issues(self, MockAuditor):
        # Setup mock
        instance = MockAuditor.return_value
        instance.run_security_scan.return_value = []
        instance.generate_report.return_value = "No issues"

        # Capture stdout to verify print
        with patch('sys.stdout', new=MagicMock()) as mock_stdout:
            with self.assertRaises(SystemExit) as cm:
                run_security(self.args)

            self.assertEqual(cm.exception.code, 0)
            instance.run_security_scan.assert_called_with(scan_type="all", severity="LOW")

    @patch("shared.security.SecurityAuditor")
    def test_run_security_high_severity(self, MockAuditor):
        # Setup mock
        instance = MockAuditor.return_value
        instance.run_security_scan.return_value = [
            {"severity": "HIGH", "message": "Bad things"}
        ]
        instance.generate_report.return_value = "Found issues"

        with patch('sys.stdout', new=MagicMock()) as mock_stdout:
            with self.assertRaises(SystemExit) as cm:
                run_security(self.args)

            self.assertEqual(cm.exception.code, 1)

    @patch("shared.security.SecurityAuditor")
    def test_run_security_output_file(self, MockAuditor):
        # Setup output file
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            self.args.output = Path(tmp.name)

        try:
            instance = MockAuditor.return_value
            instance.run_security_scan.return_value = []
            instance.generate_report.return_value = "# Report"

            with patch('sys.stdout', new=MagicMock()):
                with self.assertRaises(SystemExit) as cm:
                    run_security(self.args)

            self.assertEqual(cm.exception.code, 0)

            with open(self.args.output, 'r') as f:
                content = f.read()
                self.assertEqual(content, "# Report")
        finally:
            if self.args.output.exists():
                os.unlink(self.args.output)

if __name__ == '__main__':
    unittest.main()
