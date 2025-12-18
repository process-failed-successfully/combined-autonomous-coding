
import sys
import unittest
import asyncio
from unittest.mock import MagicMock, patch, ANY
from pathlib import Path

# Mock prometheus_client regarding telemetry
sys.modules["prometheus_client"] = MagicMock()

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import main
from shared.config import Config

class TestJiraModeIntegration(unittest.TestCase):

    @patch("main.run_gemini")
    @patch("shared.jira_client.JiraClient")
    @patch("main.parse_args")
    @patch("sys.exit") # Prevent actual exit
    def test_main_with_jira_ticket(self, mock_exit, mock_parse_args, mock_jira_class, mock_run_agent):
        """
        Test that main.py correctly initializes JiraClient, gets the ticket,
        transitions it, and passes the correct config to the agent runner.
        """
        # 1. Setup Mock Args
        mock_args = MagicMock()
        mock_args.project_dir = Path("/tmp/test_project")
        mock_args.agent = "gemini"
        mock_args.jira_ticket = "PROJ-123"
        mock_args.jira_label = None
        mock_args.sprint = False
        mock_args.max_agents = 1
        mock_args.dashboard_only = False
        mock_args.manager_frequency = None
        mock_args.manager_model = None
        mock_args.model = None
        mock_args.max_iterations = None
        mock_args.verbose = False
        mock_args.verify_creation = False
        mock_args.no_stream = False
        mock_args.spec = None
        mock_args.timeout = 600.0
        mock_args.manager_first = False
        mock_args.login = False

        mock_parse_args.return_value = mock_args

        # 2. Setup Mock Jira Client
        mock_jira_instance = MagicMock()
        mock_jira_class.return_value = mock_jira_instance
        
        mock_issue = MagicMock()
        mock_issue.key = "PROJ-123"
        mock_issue.fields.summary = "Fix the login bug"
        mock_issue.fields.description = "The login button is broken."
        
        mock_jira_instance.get_issue.return_value = mock_issue

        # 3. Setup Config Loader Mock (to provide minimal Base config)
        with patch("main.load_config_from_file") as mock_load_config:
            mock_load_config.return_value = {
                "jira": {
                    "url": "http://jira.mock",
                    "email": "test@test.com",
                    "token": "secret"
                }
            }
            
            # 4. Run Main
            # We use asyncio.run inside main, but calling main() is async.
            # In a test, we can just await it if we are in an async test, 
            # OR use asyncio.run(main()) if main were a sync wrapper.
            # main() is defined as `async def main():` in main.py.
            # So we should run it with asyncio.run()
            
            # We need to ensure that the environment variables or config are set properly.
            # The test mimics loading from config file.
            
            # Since main is async, we wrap it
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(main())
            loop.close()

        # 5. Assertions

        # Verify Jira Client Init
        mock_jira_class.assert_called_once()
        
        # Verify Ticket Fetch
        mock_jira_instance.get_issue.assert_called_with("PROJ-123")
        
        # Verify Transition
        mock_jira_instance.transition_issue.assert_called_with("PROJ-123", "In Progress")
        
        # Verify Agent Runner Call
        mock_run_agent.assert_called_once()
        
        # Extract Config passed to runner
        call_args = mock_run_agent.call_args
        config_passed = call_args[0][0]
        
        self.assertIsInstance(config_passed, Config)
        self.assertEqual(config_passed.jira_ticket_key, "PROJ-123")
        self.assertIn("JIRA TICKET PROJ-123", config_passed.jira_spec_content)
        self.assertIn("The login button is broken", config_passed.jira_spec_content)
        
        # Verify Project Name override
        # The main.py sets project_name = issue.key for ID gen, 
        # but config.project_dir remains what was passed in args.
        # ID generation uses issue.key
        self.assertIn("PROJ-123", config_passed.agent_id)

    @patch("main.run_gemini")
    @patch("shared.jira_client.JiraClient")
    @patch("main.parse_args")
    @patch("sys.exit")
    def test_main_with_jira_label(self, mock_exit, mock_parse_args, mock_jira_class, mock_run_agent):
        """Test fetching by Label."""
        mock_args = MagicMock()
        mock_args.project_dir = Path(".")
        mock_args.agent = "gemini"
        mock_args.jira_ticket = None
        mock_args.jira_label = "my-label"
        mock_args.dashboard_only = False
        # ... set other defaults as needed to avoid AttributeError
        mock_args.sprint = False
        mock_args.max_agents = 1
        mock_args.model = None
        mock_args.max_iterations = None
        mock_args.verbose = False
        mock_args.verify_creation = False
        mock_args.spec = None
        mock_args.no_stream = False
        mock_args.timeout = 600.0
        mock_args.manager_frequency = 10
        mock_args.manager_model = None
        mock_args.manager_first = False
        mock_args.login = False

        mock_parse_args.return_value = mock_args

        mock_jira_instance = MagicMock()
        mock_jira_class.return_value = mock_jira_instance
        
        mock_issue = MagicMock()
        mock_issue.key = "LABEL-1"
        mock_issue.fields.summary = "Task from label"
        mock_issue.fields.description = "Desc"
        
        mock_jira_instance.get_first_todo_by_label.return_value = mock_issue

        with patch("main.load_config_from_file") as mock_load_config:
            mock_load_config.return_value = {
                "jira": {"url": "http://j", "email": "e", "token": "t"}
            }
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(main())
            loop.close()

        mock_jira_instance.get_first_todo_by_label.assert_called_with("my-label")
        mock_jira_instance.transition_issue.assert_called_with("LABEL-1", "In Progress")
        
        call_args = mock_run_agent.call_args
        config_passed = call_args[0][0]
        self.assertEqual(config_passed.jira_ticket_key, "LABEL-1")

if __name__ == "__main__":
    unittest.main()
