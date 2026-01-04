import unittest
from unittest.mock import patch, mock_open
from pathlib import Path
import yaml
import platformdirs
import sys

# Add project root to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from main import run_configure

class TestConfigureCommand(unittest.TestCase):

    @patch('builtins.input')
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('platformdirs.user_config_dir')
    def test_run_configure_creates_config_correctly(
        self,
        mock_user_config_dir,
        mock_open_file,
        mock_path_exists,
        mock_input
    ):
        # --- Setup Mocks ---
        # Mock platformdirs to return a predictable path
        mock_config_dir = "/tmp/test_config"
        mock_user_config_dir.return_value = mock_config_dir

        config_path = Path(mock_config_dir) / "agent_config.yaml"

        # Mock Path.exists() to return False (simulating no existing file)
        mock_path_exists.return_value = False

        # Mock user input for a full configuration
        mock_input.side_effect = [
            "https://test.atlassian.net",  # Jira URL
            "test@example.com",           # Jira Email
            "jira_api_token",             # Jira Token
            "https://hooks.slack.com/...",  # Slack Webhook
            "https://discord.com/..."      # Discord Webhook
        ]

        # --- Run the function ---
        run_configure()

        # --- Assertions ---
        # 1. Check if the config file was opened for writing
        mock_open_file.assert_called_with(config_path, 'w')

        # 2. Verify the content that was written to the file
        # mock_open().write() gives access to the arguments of the write call.
        # We need to capture all calls to write.
        handle = mock_open_file()

        # Consolidate all write calls into a single string
        written_content = "".join(call.args[0] for call in handle.write.call_args_list)

        # Parse the written YAML to verify its structure and content
        written_data = yaml.safe_load(written_content)

        expected_data = {
            'jira': {
                'url': 'https://test.atlassian.net',
                'email': 'test@example.com',
                'token': 'jira_api_token'
            },
            'slack_webhook_url': 'https://hooks.slack.com/...',
            'discord_webhook_url': 'https://discord.com/...'
        }

        self.assertEqual(written_data, expected_data)

if __name__ == '__main__':
    unittest.main()
