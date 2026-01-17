import unittest
from unittest.mock import MagicMock, patch
import sys
import subprocess
from pathlib import Path

class TestMainSecurity(unittest.TestCase):

    def test_run_security_cli(self):
        # We'll use subprocess to call main.py with the security command.
        # This integration test verifies that argparse parses the command correctly
        # and calls run_security (which we can indirectly verify by exit code or output).

        # Simpler approach: Verify main.py accepts the command.
        # We can run main.py --help and check for 'security'.

        result = subprocess.run(
            [sys.executable, "main.py", "--help"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("security", result.stdout)

    @patch("shared.security.SecurityAuditor.audit")
    def test_run_security_execution(self, mock_audit):
        # Here we import main locally to avoid running it on import
        import main

        # Mock args
        args = MagicMock()
        args.project_dir = Path(".")
        args.scan_type = "all"
        args.severity = "medium"
        args.no_fail = False

        # Mock audit return
        mock_audit.return_value = {
            "summary": {"score": 90, "issues": 1},
            "findings": [
                {"issue_text": "Test Issue", "severity": "LOW", "filename": "test.py", "line_number": 1}
            ]
        }

        # Capture stdout
        with patch('sys.stdout', new_callable=unittest.mock.MagicMock) as mock_stdout:
            with self.assertRaises(SystemExit) as cm:
                main.run_security(args)

            # Should exit with 0 as severity is LOW (which is not HIGH)
            self.assertEqual(cm.exception.code, 0)

            # Check arguments passed to audit
            mock_audit.assert_called_once()
            call_args = mock_audit.call_args
            self.assertEqual(call_args[1]['scan_type'], "all")
            self.assertEqual(call_args[1]['severity'], "medium")

    @patch("shared.security.SecurityAuditor.audit")
    def test_run_security_fail_on_high(self, mock_audit):
        import main

        args = MagicMock()
        args.project_dir = Path(".")
        args.scan_type = "all"
        args.severity = "medium"
        args.no_fail = False

        mock_audit.return_value = {
            "summary": {"score": 0, "issues": 1},
            "findings": [
                {"issue_text": "Bad Issue", "severity": "HIGH", "filename": "test.py", "line_number": 1}
            ]
        }

        with patch('sys.stdout', new_callable=unittest.mock.MagicMock) as mock_stdout:
            with self.assertRaises(SystemExit) as cm:
                main.run_security(args)

            # Should exit with 1 because of HIGH severity finding
            self.assertEqual(cm.exception.code, 1)

    @patch("shared.security.SecurityAuditor.audit")
    def test_run_security_no_fail_flag(self, mock_audit):
        import main

        args = MagicMock()
        args.project_dir = Path(".")
        args.scan_type = "all"
        args.severity = "medium"
        args.no_fail = True # Flag set

        mock_audit.return_value = {
            "summary": {"score": 0, "issues": 1},
            "findings": [
                {"issue_text": "Bad Issue", "severity": "HIGH", "filename": "test.py", "line_number": 1}
            ]
        }

        with patch('sys.stdout', new_callable=unittest.mock.MagicMock) as mock_stdout:
            with self.assertRaises(SystemExit) as cm:
                main.run_security(args)

            # Should exit with 0 because --no-fail is set
            self.assertEqual(cm.exception.code, 0)

if __name__ == "__main__":
    unittest.main()
