
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys
import argparse

# Add repo root to path
sys.path.append(str(Path(__file__).parent.parent))

# Let's test the command dispatch logic in main.py by mocking sys.argv and run_coverage_logic
from main import main
import asyncio

class TestMainCoverage(unittest.IsolatedAsyncioTestCase):

    @patch("shared.coverage.run_coverage_logic")
    @patch("main.parse_args")
    async def test_main_coverage_command(self, mock_parse_args, mock_run_coverage):
        # Setup arguments as if parsed from CLI
        mock_args = MagicMock()
        mock_args.command = "coverage"
        mock_args.project_dir = Path(".")
        mock_args.html = True
        mock_args.xml = False
        mock_args.fail_under = 90
        mock_args.test_args = ["tests/"]

        # We also need to set default values for other args accessed in main()
        # but main() dispatches early based on command string.
        # Set attributes accessed later in main() to avoid AttributeError or other issues
        mock_args.jira_ticket = None
        mock_args.jira_label = None
        mock_args.profile = None
        mock_args.agent = "gemini"
        mock_args.model = None
        mock_args.max_iterations = None
        mock_args.verbose = False
        mock_args.no_stream = False
        mock_args.spec = None
        mock_args.verify_creation = False
        mock_args.manager_frequency = None
        mock_args.manager_model = None
        mock_args.manager_first = False
        mock_args.login = False
        mock_args.timeout = None
        mock_args.max_error_wait = None
        mock_args.sprint = False
        mock_args.max_agents = 1
        mock_args.dind = False
        mock_args.dashboard_url = ""


        mock_parse_args.return_value = mock_args
        mock_run_coverage.return_value = True

        # Run main (we need to be careful not to trigger sys.exit)
        # We can mock sys.exit to assert it was called with 0
        with patch("sys.exit") as mock_exit:
            await main()

            # Assert run_coverage_logic was called with correct args
            mock_run_coverage.assert_called_once_with(
                project_dir=Path("."),
                html_report=True,
                xml_report=False,
                fail_under=90,
                test_args=["tests/"]
            )

            mock_exit.assert_called_with(0)

    @patch("shared.coverage.run_coverage_logic")
    @patch("main.parse_args")
    async def test_main_coverage_failure(self, mock_parse_args, mock_run_coverage):
        mock_args = MagicMock()
        mock_args.command = "coverage"
        mock_args.project_dir = Path(".")
        mock_args.html = False
        mock_args.xml = False
        mock_args.fail_under = None
        mock_args.test_args = []

        # Set default attrs
        mock_args.jira_ticket = None
        mock_args.jira_label = None
        mock_args.profile = None
        mock_args.agent = "gemini"
        mock_args.model = None
        mock_args.max_iterations = None
        mock_args.verbose = False
        mock_args.no_stream = False
        mock_args.spec = None
        mock_args.verify_creation = False
        mock_args.manager_frequency = None
        mock_args.manager_model = None
        mock_args.manager_first = False
        mock_args.login = False
        mock_args.timeout = None
        mock_args.max_error_wait = None
        mock_args.sprint = False
        mock_args.max_agents = 1
        mock_args.dind = False
        mock_args.dashboard_url = ""

        mock_parse_args.return_value = mock_args
        mock_run_coverage.return_value = False # Simulate failure

        with patch("sys.exit") as mock_exit:
            await main()
            # If sys.exit is called with 0, then the logic in main.py is flawed or something else is happening.
            # In main.py:
            # sys.exit(0 if success else 1)
            # If success is False, it should be 1.

            mock_exit.assert_called_with(1)

if __name__ == "__main__":
    unittest.main()
