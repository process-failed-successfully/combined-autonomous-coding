
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import argparse
import io
import os
import tempfile
import yaml
from contextlib import redirect_stdout

import main

class TestDoctorCommand(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _run_doctor_with_exit_code(self, args):
        with self.assertRaises(SystemExit) as cm:
            main.run_doctor(args)
        return cm.exception.code

    @patch('shared.config_loader.platformdirs.user_config_dir')
    @patch('shutil.which')
    @patch('os.access')
    @patch('main.JiraClient')
    def test_doctor_happy_path(self, mock_jira_client, mock_os_access, mock_shutil_which, mock_user_config_dir):
        # --- Arrange ---
        # Mock config
        mock_user_config_dir.return_value = str(self.project_dir)
        config_path = self.project_dir / "agent_config.yaml"
        config_data = {
            'jira': {'url': 'https://test.atlassian.net', 'email': 'test@test.com', 'token': 'token'},
            'slack_webhook_url': 'https://hooks.slack.com/services/valid',
            'discord_webhook_url': 'https://discord.com/api/webhooks/valid'
        }
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)

        # Mock dependencies
        mock_shutil_which.side_effect = lambda cmd: f"/usr/bin/{cmd}"

        # Mock permissions
        mock_os_access.return_value = True

        # Mock Jira
        mock_jira_client.return_value.client.myself.return_value = {}

        args = argparse.Namespace(project_dir=self.project_dir)

        # --- Act ---
        f = io.StringIO()
        with redirect_stdout(f):
            exit_code = self._run_doctor_with_exit_code(args)
        output = f.getvalue()

        # --- Assert ---
        self.assertEqual(exit_code, 0)
        self.assertIn("✅ All checks passed. Your environment is ready!", output)
        self.assertIn("✅ Configuration file (agent_config.yaml) found", output)
        self.assertIn("✅ `git` command is installed and in PATH", output)
        self.assertIn("✅ `docker` command is installed and in PATH", output)
        self.assertIn("✅ Jira connection and authentication successful", output)
        self.assertIn("✅ Slack webhook URL format is valid", output)
        self.assertIn("✅ Discord webhook URL format is valid", output)
        self.assertIn("✅ Project directory is writable", output)

    @patch('shared.config_loader.platformdirs.user_config_dir')
    def test_doctor_no_config_file(self, mock_user_config_dir):
        mock_user_config_dir.return_value = "/non/existent/path"
        args = argparse.Namespace(project_dir=self.project_dir)

        f = io.StringIO()
        with redirect_stdout(f):
            exit_code = self._run_doctor_with_exit_code(args)
        output = f.getvalue()

        self.assertEqual(exit_code, 1)
        self.assertIn("❌ Configuration file (agent_config.yaml) found", output)

    @patch('shared.config_loader.platformdirs.user_config_dir')
    def test_doctor_invalid_yaml(self, mock_user_config_dir):
        mock_user_config_dir.return_value = str(self.project_dir)
        config_path = self.project_dir / "agent_config.yaml"
        with open(config_path, 'w') as f:
            f.write("jira: { url: 'bad yaml'") # Invalid YAML

        args = argparse.Namespace(project_dir=self.project_dir)

        f = io.StringIO()
        with redirect_stdout(f):
            exit_code = self._run_doctor_with_exit_code(args)
        output = f.getvalue()

        self.assertEqual(exit_code, 1)
        self.assertIn("❌ Configuration file is valid YAML", output)

    @patch('shared.config_loader.platformdirs.user_config_dir')
    @patch('shutil.which')
    def test_doctor_missing_dependencies(self, mock_shutil_which, mock_user_config_dir):
        mock_user_config_dir.return_value = str(self.project_dir)
        config_path = self.project_dir / "agent_config.yaml"
        with open(config_path, 'w') as f:
            yaml.dump({}, f)

        mock_shutil_which.return_value = None

        args = argparse.Namespace(project_dir=self.project_dir)

        f = io.StringIO()
        with redirect_stdout(f):
            exit_code = self._run_doctor_with_exit_code(args)
        output = f.getvalue()

        self.assertEqual(exit_code, 1)
        self.assertIn("❌ `git` command is installed and in PATH", output)
        self.assertIn("❌ `docker` command is installed and in PATH", output)
        self.assertIn("❌ Some checks failed.", output)

    @patch('shared.config_loader.platformdirs.user_config_dir')
    @patch('shutil.which')
    @patch('os.access')
    @patch('main.JiraClient')
    def test_doctor_jira_fails(self, mock_jira_client, mock_os_access, mock_shutil_which, mock_user_config_dir):
        mock_user_config_dir.return_value = str(self.project_dir)
        config_path = self.project_dir / "agent_config.yaml"
        config_data = {'jira': {'url': 'https://test.atlassian.net', 'email': 'test@test.com', 'token': 'bad-token'}}
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)

        mock_shutil_which.side_effect = lambda cmd: f"/usr/bin/{cmd}"
        mock_os_access.return_value = True
        mock_jira_client.return_value.client.myself.side_effect = Exception("Auth failed")

        args = argparse.Namespace(project_dir=self.project_dir)

        f = io.StringIO()
        with redirect_stdout(f):
            exit_code = self._run_doctor_with_exit_code(args)
        output = f.getvalue()

        self.assertEqual(exit_code, 1)
        self.assertIn("❌ Jira connection and authentication successful", output)
        self.assertIn("Auth failed", output)
        self.assertIn("❌ Some checks failed.", output)

    @patch('shared.config_loader.platformdirs.user_config_dir')
    @patch('shutil.which')
    @patch('os.access')
    def test_doctor_non_writable_directory(self, mock_os_access, mock_shutil_which, mock_user_config_dir):
        mock_user_config_dir.return_value = str(self.project_dir)
        config_path = self.project_dir / "agent_config.yaml"
        with open(config_path, 'w') as f:
            yaml.dump({}, f)

        mock_shutil_which.side_effect = lambda cmd: f"/usr/bin/{cmd}"
        mock_os_access.return_value = False

        args = argparse.Namespace(project_dir=self.project_dir)

        f = io.StringIO()
        with redirect_stdout(f):
            exit_code = self._run_doctor_with_exit_code(args)
        output = f.getvalue()

        self.assertEqual(exit_code, 1)
        self.assertIn("❌ Project directory is writable", output)
        self.assertIn("❌ Some checks failed.", output)

if __name__ == '__main__':
    unittest.main()
