import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path
import asyncio

# Import main to access the functions we added
import main

class TestDiskUsageCLI(unittest.TestCase):

    @patch("shared.tui.AgentTUI")
    def test_run_disk_usage_function(self, mock_tui_class):
        # Setup mock
        mock_app = MagicMock()
        mock_tui_class.return_value = mock_app

        args = MagicMock()
        args.project_dir = Path("/tmp/test")

        # Call the function directly
        with self.assertRaises(SystemExit) as cm:
            main.run_disk_usage(args)

        # Verify
        self.assertEqual(cm.exception.code, 0)
        mock_tui_class.assert_called_once_with(project_dir=args.project_dir, start_tab="tab-disk-usage")
        mock_app.run.assert_called_once()

    @patch("main.run_disk_usage")
    def test_main_dispatch_disk_usage(self, mock_run):
        # We assume sys.argv is patched to include "disk-usage"
        # We need to mock everything main() calls to reach dispatch

        with patch("main.parse_args") as mock_parse:
            mock_args = MagicMock()
            mock_args.command = "disk-usage"
            mock_args.project_dir = Path(".")
            # Mock other required args
            mock_args.profile = None
            mock_args.verbose = False
            mock_args.no_stream = True
            mock_args.spec = None
            mock_args.jira_ticket = None
            mock_args.jira_label = None
            mock_args.agent = "gemini"
            mock_args.model = None
            mock_args.max_iterations = None
            mock_args.manager_frequency = None
            mock_args.manager_model = None
            mock_args.manager_first = False
            mock_args.login = False
            mock_args.timeout = None
            mock_args.max_error_wait = None
            mock_args.sprint = False
            mock_args.max_agents = None
            mock_args.dind = False
            mock_args.jira_label = None
            mock_args.jira_ticket = None
            mock_args.verify_creation = False
            mock_args.dashboard_url = None

            mock_parse.return_value = mock_args

            with patch("main.Config"), \
                 patch("main.setup_logger", return_value=(MagicMock(), MagicMock())), \
                 patch("main.load_config_from_file", return_value={}), \
                 patch("main.ensure_config_exists"), \
                 patch("shared.database.init_db"), \
                 patch("main.ensure_git_safe"), \
                 patch("shared.agent_client.AgentClient"):

                # Run main()
                try:
                    asyncio.run(main.main())
                except SystemExit:
                    pass

                mock_run.assert_called_once()

if __name__ == "__main__":
    unittest.main()
