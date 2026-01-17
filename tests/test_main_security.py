import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os
import argparse
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import main after setting path
from main import run_security

class TestMainSecurity(unittest.IsolatedAsyncioTestCase):

    @patch("main.SecurityAuditor")
    async def test_run_security_command(self, MockSecurityAuditor):
        # Setup mock args
        args = argparse.Namespace(
            project_dir=Path("."),
            severity="medium",
            ignore_failure=False
        )

        # Setup mock auditor
        mock_auditor = MockSecurityAuditor.return_value
        mock_auditor.run_all = AsyncMock() # Now run_all is properly awaited in main
        mock_auditor.results = {"summary": {"total_issues": 0}}

        # Run command
        try:
            await run_security(args)
        except SystemExit as e:
            self.assertEqual(e.code, 0)

        MockSecurityAuditor.assert_called_once()
        mock_auditor.run_all.assert_awaited_once()
        mock_auditor.print_report.assert_called_once()

    @patch("main.SecurityAuditor")
    async def test_run_security_failure_exit(self, MockSecurityAuditor):
        args = argparse.Namespace(
            project_dir=Path("."),
            severity="high",
            ignore_failure=False
        )

        mock_auditor = MockSecurityAuditor.return_value
        mock_auditor.run_all = AsyncMock()
        mock_auditor.results = {"summary": {"total_issues": 5}}

        with self.assertRaises(SystemExit) as cm:
            await run_security(args)

        self.assertEqual(cm.exception.code, 1)

if __name__ == "__main__":
    unittest.main()
