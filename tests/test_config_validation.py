
import unittest
from unittest.mock import patch, mock_open, MagicMock
import sys
from pathlib import Path
import tempfile
import yaml

# Add project root to sys.path to allow imports from shared
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import run_validate

class TestConfigValidation(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def write_config(self, data):
        config_path = self.temp_path / "agent_config.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(data, f)
        return config_path

    @patch('sys.stdout', new_callable=MagicMock)
    @patch('shared.config_loader.load_config_from_file')
    @patch('shared.config_loader.get_config_path')
    def test_valid_config(self, mock_get_config_path, mock_load_config, mock_stdout):
        """Test a completely valid configuration."""
        valid_data = {
            'model': 'gemini-1.5-pro',
            'max_iterations': 50,
            'jira': {
                'url': 'https://test.atlassian.net',
                'email': 'test@example.com',
                'token': 'secret-token'
            },
            'slack_webhook_url': 'https://hooks.slack.com/services/FAKE',
            'discord_webhook_url': 'https://discord.com/api/webhooks/FAKE'
        }
        config_path = self.write_config(valid_data)
        mock_get_config_path.return_value = config_path
        mock_load_config.return_value = valid_data

        with self.assertRaises(SystemExit) as cm:
            run_validate()

        self.assertEqual(cm.exception.code, 0)
        # It's tricky to assert on stdout with mock, better to check exit code
        # and trust the print statements for manual verification.

    @patch('sys.stdout', new_callable=MagicMock)
    @patch('shared.config_loader.get_config_path')
    def test_missing_config_file(self, mock_get_config_path, mock_stdout):
        """Test when no config file is found."""
        mock_get_config_path.return_value = None

        with self.assertRaises(SystemExit) as cm:
            run_validate()

        self.assertEqual(cm.exception.code, 1)

    @patch('sys.stdout', new_callable=MagicMock)
    @patch('shared.config_loader.load_config_from_file')
    @patch('shared.config_loader.get_config_path')
    def test_invalid_yaml(self, mock_get_config_path, mock_load_config, mock_stdout):
        """Test with a syntactically incorrect YAML file."""
        config_path = self.temp_path / "agent_config.yaml"
        with open(config_path, 'w') as f:
            f.write("jira: { url: 'test',") # Invalid YAML

        mock_get_config_path.return_value = config_path
        mock_load_config.side_effect = yaml.YAMLError("YAML parsing failed")

        with self.assertRaises(SystemExit) as cm:
            run_validate()

        self.assertEqual(cm.exception.code, 1)

    @patch('sys.stdout', new_callable=MagicMock)
    @patch('shared.config_loader.load_config_from_file')
    @patch('shared.config_loader.get_config_path')
    def test_missing_jira_keys(self, mock_get_config_path, mock_load_config, mock_stdout):
        """Test Jira config with missing required keys."""
        invalid_data = {
            'jira': {
                'url': 'https://test.atlassian.net',
                'email': 'test@example.com'
                # Missing token
            }
        }
        config_path = self.write_config(invalid_data)
        mock_get_config_path.return_value = config_path
        mock_load_config.return_value = invalid_data

        with self.assertRaises(SystemExit) as cm:
            run_validate()

        self.assertEqual(cm.exception.code, 1)

    @patch('sys.stdout', new_callable=MagicMock)
    @patch('shared.config_loader.load_config_from_file')
    @patch('shared.config_loader.get_config_path')
    def test_invalid_slack_url(self, mock_get_config_path, mock_load_config, mock_stdout):
        """Test with an invalid Slack webhook URL."""
        invalid_data = {'slack_webhook_url': 'https://wrong.url.com/FAKE'}
        config_path = self.write_config(invalid_data)
        mock_get_config_path.return_value = config_path
        mock_load_config.return_value = invalid_data

        with self.assertRaises(SystemExit) as cm:
            run_validate()

        self.assertEqual(cm.exception.code, 1)

    @patch('sys.stdout', new_callable=MagicMock)
    @patch('shared.config_loader.load_config_from_file')
    @patch('shared.config_loader.get_config_path')
    def test_invalid_discord_url(self, mock_get_config_path, mock_load_config, mock_stdout):
        """Test with an invalid Discord webhook URL."""
        invalid_data = {'discord_webhook_url': 'https://wrong.url.com/FAKE'}
        config_path = self.write_config(invalid_data)
        mock_get_config_path.return_value = config_path
        mock_load_config.return_value = invalid_data

        with self.assertRaises(SystemExit) as cm:
            run_validate()

        self.assertEqual(cm.exception.code, 1)

    @patch('sys.stdout', new_callable=MagicMock)
    @patch('shared.config_loader.load_config_from_file')
    @patch('shared.config_loader.get_config_path')
    def test_incorrect_data_type(self, mock_get_config_path, mock_load_config, mock_stdout):
        """Test a key with an incorrect data type."""
        invalid_data = {'max_iterations': 'fifty'} # Should be int
        config_path = self.write_config(invalid_data)
        mock_get_config_path.return_value = config_path
        mock_load_config.return_value = invalid_data

        with self.assertRaises(SystemExit) as cm:
            run_validate()

        self.assertEqual(cm.exception.code, 1)

