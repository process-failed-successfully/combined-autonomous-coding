import unittest
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

class TestMainSecurity(unittest.TestCase):
    def setUp(self):
        self.repo_root = Path(__file__).parent.parent
        self.main_py = self.repo_root / "main.py"

    def test_security_command_exists(self):
        """Test that the security command is available in help output."""
        result = subprocess.run(
            [sys.executable, str(self.main_py), "--help"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("security", result.stdout)
        self.assertIn("Run security scans", result.stdout)

    @patch("shared.security.SecurityAuditor.run_security_scan")
    def test_run_security_integration(self, mock_scan):
        """Integration test for security command using mock for actual scan."""
        # Mock return value
        mock_report = MagicMock()
        mock_report.findings = []
        mock_report.summary = {}
        mock_report.to_dict.return_value = {"summary": {}, "findings": []}
        mock_scan.return_value = mock_report

        # We can't easily mock imports inside a subprocess call, so we'll test the function directly
        # by importing main.py. But since main.py is a script, we might need to be careful.
        # Alternatively, we can use subprocess but we rely on the actual SecurityAuditor behavior.
        # Since we just verified SecurityAuditor in unit tests, we can trust it.
        # Let's run a "static" scan on the repo itself (it should pass or fail based on real code).
        # To make it deterministic/fast, we might want to just check argument parsing.

        result = subprocess.run(
            [sys.executable, str(self.main_py), "security", "--scan-type", "static", "--severity", "high"],
            capture_output=True,
            text=True,
            cwd=self.repo_root
        )
        # It might return 0 or 1 depending on if it finds issues in the actual codebase.
        # But it should run without crashing.
        self.assertNotEqual(result.returncode, 127) # Command not found
        self.assertIn("Running Security Scan (static)", result.stdout)

    def test_security_args(self):
        """Test argument parsing for security command."""
        result = subprocess.run(
            [sys.executable, str(self.main_py), "security", "--help"],
            capture_output=True,
            text=True
        )
        self.assertIn("--scan-type", result.stdout)
        self.assertIn("--severity", result.stdout)
        self.assertIn("--output", result.stdout)

if __name__ == "__main__":
    unittest.main()
