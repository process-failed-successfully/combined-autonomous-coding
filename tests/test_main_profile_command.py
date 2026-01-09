import unittest
from unittest.mock import patch, MagicMock, call
import os
import sys
import yaml
from pathlib import Path
import tempfile
import shutil
from io import StringIO

from main import run_profile

class TestProfileCommand(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "agent_config.yaml"

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def _write_config(self, data):
        with open(self.config_path, 'w') as f:
            yaml.dump(data, f)

    @patch('sys.stdout', new_callable=StringIO)
    @patch('platformdirs.user_config_dir')
    def test_list_profiles_no_profiles_key(self, mock_user_config_dir, mock_stdout):
        mock_user_config_dir.return_value = self.temp_dir
        self._write_config({'model': 'gemini-1.5-pro'})

        args = MagicMock(action='list', profile_name=None)
        with self.assertRaises(SystemExit) as cm:
            run_profile(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertIn("No profiles found.", mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    @patch('platformdirs.user_config_dir')
    def test_list_profiles_empty(self, mock_user_config_dir, mock_stdout):
        mock_user_config_dir.return_value = self.temp_dir
        self._write_config({'profiles': {}})

        args = MagicMock(action='list', profile_name=None)
        with self.assertRaises(SystemExit) as cm:
            run_profile(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertIn("No profiles found.", mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    @patch('platformdirs.user_config_dir')
    def test_list_profiles_with_data(self, mock_user_config_dir, mock_stdout):
        mock_user_config_dir.return_value = self.temp_dir
        self._write_config({
            'profiles': {
                'work': {'model': 'gemini-1.5-pro'},
                'personal': {'model': 'claude-3-opus'}
            }
        })

        args = MagicMock(action='list', profile_name=None)
        with self.assertRaises(SystemExit) as cm:
            run_profile(args)

        self.assertEqual(cm.exception.code, 0)
        output = mock_stdout.getvalue()
        self.assertIn("- work", output)
        self.assertIn("- personal", output)

    @patch('sys.stdout', new_callable=StringIO)
    @patch('platformdirs.user_config_dir')
    def test_show_profile_exists(self, mock_user_config_dir, mock_stdout):
        mock_user_config_dir.return_value = self.temp_dir
        self._write_config({
            'profiles': {
                'work': {'model': 'gemini-1.5-pro', 'agent': 'gemini'}
            }
        })

        args = MagicMock(action='show', profile_name='work')
        with self.assertRaises(SystemExit) as cm:
            run_profile(args)

        self.assertEqual(cm.exception.code, 0)
        output = mock_stdout.getvalue()
        self.assertIn("agent: gemini", output)
        self.assertIn("model: gemini-1.5-pro", output)

    @patch('sys.stderr', new_callable=StringIO)
    @patch('platformdirs.user_config_dir')
    def test_show_profile_not_found(self, mock_user_config_dir, mock_stderr):
        mock_user_config_dir.return_value = self.temp_dir
        self._write_config({'profiles': {}})

        args = MagicMock(action='show', profile_name='nonexistent')
        with self.assertRaises(SystemExit) as cm:
            run_profile(args)

        self.assertEqual(cm.exception.code, 1)
        self.assertIn("Profile 'nonexistent' not found.", mock_stderr.getvalue())

    @patch('builtins.input', return_value='y')
    @patch('sys.stdout', new_callable=StringIO)
    @patch('platformdirs.user_config_dir')
    def test_delete_profile_confirm_yes(self, mock_user_config_dir, mock_stdout, mock_input):
        mock_user_config_dir.return_value = self.temp_dir
        self._write_config({'profiles': {'work': {'model': 'gemini-1.5-pro'}}})

        args = MagicMock(action='delete', profile_name='work', yes=False)
        with self.assertRaises(SystemExit) as cm:
            run_profile(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertIn("Profile 'work' deleted successfully.", mock_stdout.getvalue())

        with open(self.config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        self.assertNotIn('work', config_data['profiles'])

    @patch('builtins.input', return_value='n')
    @patch('sys.stdout', new_callable=StringIO)
    @patch('platformdirs.user_config_dir')
    def test_delete_profile_confirm_no(self, mock_user_config_dir, mock_stdout, mock_input):
        mock_user_config_dir.return_value = self.temp_dir
        self._write_config({'profiles': {'work': {'model': 'gemini-1.5-pro'}}})

        args = MagicMock(action='delete', profile_name='work', yes=False)
        with self.assertRaises(SystemExit) as cm:
            run_profile(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertIn("Aborted.", mock_stdout.getvalue())

        with open(self.config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        self.assertIn('work', config_data['profiles'])

    @patch('sys.stdout', new_callable=StringIO)
    @patch('platformdirs.user_config_dir')
    def test_delete_profile_with_yes_flag(self, mock_user_config_dir, mock_stdout):
        mock_user_config_dir.return_value = self.temp_dir
        self._write_config({'profiles': {'work': {'model': 'gemini-1.5-pro'}}})

        args = MagicMock(action='delete', profile_name='work', yes=True)
        with self.assertRaises(SystemExit) as cm:
            run_profile(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertIn("Profile 'work' deleted successfully.", mock_stdout.getvalue())

        with open(self.config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        self.assertNotIn('work', config_data['profiles'])

    @patch('builtins.input', side_effect=['gemini-1.5-pro', 'gemini', 'http://jira.test.com', 'test@test.com', 'token123'])
    @patch('sys.stdout', new_callable=StringIO)
    @patch('platformdirs.user_config_dir')
    def test_create_profile(self, mock_user_config_dir, mock_stdout, mock_input):
        mock_user_config_dir.return_value = self.temp_dir
        self._write_config({})

        args = MagicMock(action='create', profile_name='new_profile')
        with self.assertRaises(SystemExit) as cm:
            run_profile(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertIn("Profile 'new_profile' created successfully.", mock_stdout.getvalue())

        with open(self.config_path, 'r') as f:
            config_data = yaml.safe_load(f)

        self.assertIn('new_profile', config_data['profiles'])
        profile = config_data['profiles']['new_profile']
        self.assertEqual(profile['model'], 'gemini-1.5-pro')
        self.assertEqual(profile['agent'], 'gemini')
        self.assertEqual(profile['jira']['url'], 'http://jira.test.com')

    @patch('sys.stderr', new_callable=StringIO)
    @patch('platformdirs.user_config_dir')
    def test_create_profile_already_exists(self, mock_user_config_dir, mock_stderr):
        mock_user_config_dir.return_value = self.temp_dir
        self._write_config({'profiles': {'existing': {'model': 'gemini'}}})

        args = MagicMock(action='create', profile_name='existing')
        with self.assertRaises(SystemExit) as cm:
            run_profile(args)

        self.assertEqual(cm.exception.code, 1)
        self.assertIn("Profile 'existing' already exists.", mock_stderr.getvalue())

if __name__ == '__main__':
    unittest.main()
