import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import argparse
from pathlib import Path
import asyncio

# Import main (will need to patch sys.modules to avoid issues if needed, or just import)
import main

class TestMainSecurity(unittest.TestCase):

    @patch("shared.security.SecurityAuditor")
    @patch("sys.stdout", new_callable=MagicMock) # Capture print output
    def test_run_security_command(self, mock_print, MockAuditor):
        # Setup arguments
        args = argparse.Namespace(
            project_dir=Path("."),
            scan_type="all",
            severity="LOW",
            output=None,
            command="security"
        )

        # Setup mock auditor
        instance = MockAuditor.return_value
        instance.run_bandit.return_value = [{"issue": "bandit"}]
        instance.scan_secrets.return_value = [{"issue": "secret"}]
        instance.generate_report.return_value = "Report Content"

        # Run the command (it's async)
        with patch("sys.exit"): # Prevent exit
            asyncio.run(main.run_security(args))

        # Verify calls
        instance.run_bandit.assert_called_once_with(severity="LOW")
        instance.scan_secrets.assert_called_once()
        instance.generate_report.assert_called_once()

        # Verify output printed
        printed_output = "".join(call.args[0] for call in mock_print.write.call_args_list)
        self.assertIn("Report Content", printed_output)

    @patch("shared.security.SecurityAuditor")
    def test_run_security_save_output(self, MockAuditor):
        output_file = Path("security_report.md")
        args = argparse.Namespace(
            project_dir=Path("."),
            scan_type="bandit",
            severity="HIGH",
            output=output_file,
            command="security"
        )

        instance = MockAuditor.return_value
        instance.run_bandit.return_value = []
        instance.scan_secrets.return_value = [] # Should not be called but good to mock
        instance.generate_report.return_value = "Report Content"

        # Mock file writing
        with patch.object(Path, 'write_text') as mock_write:
            with patch("sys.exit"): # Prevent exit
                asyncio.run(main.run_security(args))
            mock_write.assert_called_once_with("Report Content", encoding="utf-8")

        # Verify Bandit called, Secrets NOT called
        instance.run_bandit.assert_called_once_with(severity="HIGH")
        instance.scan_secrets.assert_not_called()

if __name__ == '__main__':
    unittest.main()
