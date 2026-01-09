
import unittest
import io
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import shutil
import yaml

from main import run_config

class TestMainConfigCommand(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir)
        self.config_path = self.config_dir / "agent_config.yaml"

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    @patch('platformdirs.user_config_dir')
    def test_config_list_empty(self, mock_user_config_dir):
        mock_user_config_dir.return_value = self.temp_dir
        args = MagicMock(action="list", key=None, value=None)

        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            result = run_config(args)
            self.assertEqual(result, 0)
            self.assertIn("Configuration is empty", mock_stdout.getvalue())

    @patch('platformdirs.user_config_dir')
    def test_config_list_with_data(self, mock_user_config_dir):
        mock_user_config_dir.return_value = self.temp_dir
        config_data = {'model': 'gemini-1.5-pro', 'max_iterations': 10}
        with open(self.config_path, 'w') as f:
            yaml.dump(config_data, f)

        args = MagicMock(action="list", key=None, value=None)

        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            result = run_config(args)
            self.assertEqual(result, 0)
            output = mock_stdout.getvalue()
            self.assertIn("model: gemini-1.5-pro", output)
            self.assertIn("max_iterations: 10", output)

    @patch('platformdirs.user_config_dir')
    def test_config_get_existing_key(self, mock_user_config_dir):
        mock_user_config_dir.return_value = self.temp_dir
        config_data = {'model': 'gemini-1.5-pro'}
        with open(self.config_path, 'w') as f:
            yaml.dump(config_data, f)

        args = MagicMock(action="get", key="model", value=None)

        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            result = run_config(args)
            self.assertEqual(result, 0)
            self.assertEqual("gemini-1.5-pro\n", mock_stdout.getvalue())

    @patch('platformdirs.user_config_dir')
    def test_config_get_non_existing_key(self, mock_user_config_dir):
        mock_user_config_dir.return_value = self.temp_dir
        args = MagicMock(action="get", key="non_existing_key", value=None)

        with patch('sys.stderr', new_callable=io.StringIO) as mock_stderr:
            result = run_config(args)
            self.assertEqual(result, 1)
            self.assertIn("Key 'non_existing_key' not found", mock_stderr.getvalue())

    @patch('platformdirs.user_config_dir')
    def test_config_set_new_key(self, mock_user_config_dir):
        mock_user_config_dir.return_value = self.temp_dir
        args = MagicMock(action="set", key="model", value="gemini-1.5-pro")

        result = run_config(args)
        self.assertEqual(result, 0)

        with open(self.config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        self.assertEqual(config_data, {'model': 'gemini-1.5-pro'})

    @patch('platformdirs.user_config_dir')
    def test_config_set_nested_key(self, mock_user_config_dir):
        mock_user_config_dir.return_value = self.temp_dir
        args = MagicMock(action="set", key="jira.url", value="https://example.atlassian.net")
        result = run_config(args)
        self.assertEqual(result, 0)
        with open(self.config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        self.assertEqual(config_data, {'jira': {'url': 'https://example.atlassian.net'}})

    @patch('platformdirs.user_config_dir')
    def test_config_set_overwrite_key(self, mock_user_config_dir):
        mock_user_config_dir.return_value = self.temp_dir
        config_data = {'model': 'gemini-1.0-pro'}
        with open(self.config_path, 'w') as f:
            yaml.dump(config_data, f)

        args = MagicMock(action="set", key="model", value="gemini-1.5-pro")
        result = run_config(args)
        self.assertEqual(result, 0)

        with open(self.config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        self.assertEqual(config_data, {'model': 'gemini-1.5-pro'})

    @patch('platformdirs.user_config_dir')
    def test_config_set_type_parsing(self, mock_user_config_dir):
        mock_user_config_dir.return_value = self.temp_dir

        # Test integer
        args = MagicMock(action="set", key="max_iterations", value="20")
        self.assertEqual(run_config(args), 0)
        with open(self.config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        self.assertEqual(config_data['max_iterations'], 20)

        # Test float
        args = MagicMock(action="set", key="temperature", value="0.8")
        self.assertEqual(run_config(args), 0)
        with open(self.config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        self.assertEqual(config_data['temperature'], 0.8)

        # Test boolean true
        args = MagicMock(action="set", key="stream_output", value="true")
        self.assertEqual(run_config(args), 0)
        with open(self.config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        self.assertEqual(config_data['stream_output'], True)

        # Test boolean false
        args = MagicMock(action="set", key="stream_output", value="False")
        self.assertEqual(run_config(args), 0)
        with open(self.config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        self.assertEqual(config_data['stream_output'], False)


if __name__ == '__main__':
    unittest.main()
