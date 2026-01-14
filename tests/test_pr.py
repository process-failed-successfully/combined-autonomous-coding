import unittest
from unittest.mock import patch, MagicMock
from io import StringIO
import sys
from pathlib import Path
import argparse

# Add the root directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from main import run_pr

class TestPRCommand(unittest.TestCase):

    def setUp(self):
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        sys.stdout = self.stdout = StringIO()
        sys.stderr = self.stderr = StringIO()

    def tearDown(self):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr

    @patch('main.load_config_from_file')
    @patch('main._pr_list')
    def test_run_pr_list(self, mock_pr_list, mock_load_config):
        mock_load_config.return_value = {'github_token': 'fake_token'}
        args = argparse.Namespace(action='list', project_dir=Path('.'), profile=None)
        run_pr(args)
        mock_pr_list.assert_called_once()

    @patch('main.load_config_from_file')
    @patch('main._pr_checkout')
    def test_run_pr_checkout(self, mock_pr_checkout, mock_load_config):
        mock_load_config.return_value = {'github_token': 'fake_token'}
        args = argparse.Namespace(action='checkout', pr_number=123, project_dir=Path('.'), profile=None)
        run_pr(args)
        mock_pr_checkout.assert_called_once()

    @patch('main.load_config_from_file')
    @patch('shared.github_client.GitHubClient.list_pull_requests')
    def test_pr_list_success(self, mock_list_prs, mock_load_config):
        mock_load_config.return_value = {'github_token': 'test_token'}
        mock_prs_data = [
            {'number': 1, 'title': 'Feat: Implement PR functionality', 'user': {'login': 'testuser'}, 'head': {'ref': 'feature-branch'}}
        ]
        mock_list_prs.return_value = mock_prs_data

        from main import _pr_list
        args = argparse.Namespace(project_dir=Path('.'))
        with self.assertRaises(SystemExit) as cm:
            _pr_list(args, argparse.Namespace(github_token='test_token', github_host=None))

        self.assertEqual(cm.exception.code, 0)
        output = self.stdout.getvalue()
        self.assertIn('#1', output)
        self.assertIn('Feat: Implement PR functionality', output)
        self.assertIn('testuser', output)
        self.assertIn('feature-branch', output)

    @patch('main.shutil.which', return_value='/usr/bin/git')
    @patch('main.subprocess.run')
    @patch('main.load_config_from_file')
    @patch('shared.github_client.GitHubClient.get_pull_request')
    def test_pr_checkout_success(self, mock_get_pr, mock_load_config, mock_subprocess_run, mock_which):
        mock_load_config.return_value = {'github_token': 'test_token'}
        mock_get_pr.return_value = {'head': {'ref': 'feature-branch'}}

        # Mock subprocess.run to return a successful result
        mock_subprocess_run.return_value = MagicMock(returncode=0, stdout='', stderr='')

        from main import _pr_checkout
        args = argparse.Namespace(pr_number=1, project_dir=Path('.'))

        with patch('pathlib.Path.is_dir', return_value=True):
            with self.assertRaises(SystemExit) as cm:
                _pr_checkout(args, argparse.Namespace(github_token='test_token', github_host=None))

        self.assertEqual(cm.exception.code, 0)
        self.assertIn("Successfully checked out branch 'feature-branch'", self.stdout.getvalue())

if __name__ == '__main__':
    unittest.main()
