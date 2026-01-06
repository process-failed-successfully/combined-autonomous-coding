import unittest
from unittest.mock import patch, MagicMock
import argparse
from pathlib import Path
import os
import sys
import yaml

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import run_doctor

class TestDoctorCommand(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory and argparse.Namespace for each test."""
        self.test_dir = Path("test_project_dir")
        self.test_dir.mkdir(exist_ok=True)
        self.args = argparse.Namespace(project_dir=self.test_dir)

    def tearDown(self):
        """Clean up the temporary directory after each test."""
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        config_path = Path("agent_config.yaml")
        if config_path.exists():
            config_path.unlink()

    @patch('shared.config_loader.get_config_path')
    @patch('shared.config_loader.load_config_from_file')
    @patch('shutil.which', return_value="/usr/bin/git")
    @patch('os.access', return_value=True)
    @patch('requests.head')
    def test_doctor_all_checks_pass(self, mock_requests_head, mock_os_access, mock_shutil_which, mock_load_config, mock_get_config_path):
        """Test the doctor command when all checks pass."""
        # Arrange
        config_path = self.test_dir / "agent_config.yaml"
        config_path.touch()
        mock_get_config_path.return_value = config_path
        mock_load_config.return_value = {}

        # Act & Assert
        with self.assertRaises(SystemExit) as cm:
            run_doctor(self.args)
        self.assertEqual(cm.exception.code, 0)

    @patch('shared.config_loader.get_config_path', return_value=None)
    def test_doctor_no_config_file(self, mock_get_config_path):
        """Test the doctor command when the config file is not found."""
        # Act & Assert
        with self.assertRaises(SystemExit) as cm:
            run_doctor(self.args)
        self.assertEqual(cm.exception.code, 1)

    @patch('shared.config_loader.get_config_path')
    @patch('shared.config_loader.load_config_from_file')
    def test_doctor_malformed_config_file(self, mock_load_config, mock_get_config_path):
        """Test the doctor command with a malformed YAML config file."""
        # Arrange
        config_path = self.test_dir / "agent_config.yaml"
        # This write is not strictly needed since we mock the load, but good practice
        config_path.write_text("this is not valid yaml:")
        mock_get_config_path.return_value = config_path
        mock_load_config.side_effect = yaml.YAMLError("Malformed YAML")

        # Act & Assert
        with self.assertRaises(SystemExit) as cm:
            run_doctor(self.args)
        self.assertEqual(cm.exception.code, 1)

    @patch('shared.config_loader.get_config_path')
    @patch('shared.config_loader.load_config_from_file')
    @patch('shutil.which', return_value="/usr/bin/git")
    @patch('os.access', return_value=True)
    def test_doctor_invalid_jira_config(self, mock_os_access, mock_shutil_which, mock_load_config, mock_get_config_path):
        """Test doctor with a config file that has invalid Jira details."""
        # Arrange
        config_path = self.test_dir / "agent_config.yaml"
        config_path.touch()
        mock_get_config_path.return_value = config_path
        mock_load_config.return_value = {
            'jira': {
                'url': 'https://test.atlassian.net',
                # Missing email and token
            }
        }

        # Act & Assert
        with self.assertRaises(SystemExit) as cm:
            run_doctor(self.args)
        self.assertEqual(cm.exception.code, 1)

    @patch('shared.config_loader.get_config_path')
    @patch('shared.config_loader.load_config_from_file')
    @patch('shutil.which', return_value="/usr/bin/git")
    @patch('os.access', return_value=True)
    def test_doctor_invalid_webhook_format(self, mock_os_access, mock_shutil_which, mock_load_config, mock_get_config_path):
        """Test doctor with an invalidly formatted webhook URL."""
        # Arrange
        config_path = self.test_dir / "agent_config.yaml"
        config_path.touch()
        mock_get_config_path.return_value = config_path
        mock_load_config.return_value = {
            'slack_webhook_url': 'https://not-slack.com/fake'
        }

        # Act & Assert
        with self.assertRaises(SystemExit) as cm:
            run_doctor(self.args)
        self.assertEqual(cm.exception.code, 1)

    @patch('shared.config_loader.get_config_path')
    @patch('shared.config_loader.load_config_from_file')
    @patch('shutil.which', return_value=None)
    def test_doctor_git_not_found(self, mock_shutil_which, mock_load_config, mock_get_config_path):
        """Test the doctor command when git is not installed."""
        # Arrange
        config_path = self.test_dir / "agent_config.yaml"
        config_path.touch()
        mock_get_config_path.return_value = config_path
        mock_load_config.return_value = {}

        # Act & Assert
        with self.assertRaises(SystemExit) as cm:
            run_doctor(self.args)
        self.assertEqual(cm.exception.code, 1)

    @patch('shared.config_loader.get_config_path')
    @patch('shared.config_loader.load_config_from_file')
    @patch('shutil.which', return_value="/usr/bin/git")
    @patch('os.access', return_value=False)
    def test_doctor_directory_not_writable(self, mock_os_access, mock_shutil_which, mock_load_config, mock_get_config_path):
        """Test the doctor command when the project directory is not writable."""
        # Arrange
        config_path = self.test_dir / "agent_config.yaml"
        config_path.touch()
        mock_get_config_path.return_value = config_path
        mock_load_config.return_value = {}

        # Act & Assert
        with self.assertRaises(SystemExit) as cm:
            run_doctor(self.args)
        self.assertEqual(cm.exception.code, 1)

    @patch('shared.config_loader.get_config_path')
    @patch('shared.config_loader.load_config_from_file')
    @patch('shutil.which', return_value="/usr/bin/git")
    @patch('os.access', return_value=True)
    @patch('shared.jira_client.JiraClient')
    def test_doctor_jira_connection_fails(self, mock_jira_client, mock_os_access, mock_shutil_which, mock_load_config, mock_get_config_path):
        """Test the doctor command when Jira connection fails."""
        # Arrange
        config_path = self.test_dir / "agent_config.yaml"
        config_path.touch()
        mock_get_config_path.return_value = config_path
        mock_load_config.return_value = {
            'jira': {
                'url': 'https://test.atlassian.net',
                'email': 'test@example.com',
                'token': 'fake-token'
            }
        }
        mock_jira_client.return_value.check_connection.side_effect = Exception("Jira connection failed")

        # Act & Assert
        with self.assertRaises(SystemExit) as cm:
            run_doctor(self.args)
        self.assertEqual(cm.exception.code, 1)

    @patch('shared.config_loader.get_config_path')
    @patch('shared.config_loader.load_config_from_file')
    @patch('shutil.which', return_value="/usr/bin/git")
    @patch('os.access', return_value=True)
    @patch('requests.head')
    def test_doctor_webhook_fails(self, mock_requests_head, mock_os_access, mock_shutil_which, mock_load_config, mock_get_config_path):
        """Test the doctor command when a webhook check fails."""
        # Arrange
        config_path = self.test_dir / "agent_config.yaml"
        config_path.touch()
        mock_get_config_path.return_value = config_path
        mock_load_config.return_value = {
            'slack_webhook_url': 'https://hooks.slack.com/services/fake'
        }
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_requests_head.return_value = mock_response

        # Act & Assert
        with self.assertRaises(SystemExit) as cm:
            run_doctor(self.args)
        self.assertEqual(cm.exception.code, 1)

    @patch('shared.config_loader.get_config_path')
    @patch('shared.config_loader.load_config_from_file')
    @patch('shutil.which', return_value=None) # First failure
    @patch('os.access', return_value=False) # Second failure
    def test_doctor_multiple_failures(self, mock_os_access, mock_shutil_which, mock_load_config, mock_get_config_path):
        """Test the doctor command with multiple simultaneous failures."""
        # Arrange
        config_path = self.test_dir / "agent_config.yaml"
        config_path.touch()
        mock_get_config_path.return_value = config_path
        # Also, an invalid Jira config to add a third failure
        mock_load_config.return_value = {
            'jira': { 'url': 'https://test.atlassian.net' }
        }

        # Act & Assert
        with self.assertRaises(SystemExit) as cm:
            run_doctor(self.args)
        self.assertEqual(cm.exception.code, 1)

if __name__ == '__main__':
    unittest.main()
