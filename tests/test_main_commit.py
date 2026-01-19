import unittest
from unittest.mock import patch, call, MagicMock
from main import run_commit
import argparse
from pathlib import Path

class TestCommitCommand(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        # This mock will be active for all tests in this class
        self.mock_subprocess_patcher = patch('subprocess.run')
        self.mock_subprocess_run = self.mock_subprocess_patcher.start()

        def side_effect(*args, **kwargs):
            command = args[0]
            if 'diff' in command:
                # Simulate that there are changes to commit
                return MagicMock(returncode=1)
            # For 'add' and 'commit', simulate success
            return MagicMock(returncode=0, stdout="Success")

        self.mock_subprocess_run.side_effect = side_effect

    def tearDown(self):
        self.mock_subprocess_patcher.stop()

    @patch('builtins.input')
    @patch('shutil.which', return_value='/usr/bin/git')
    @patch('pathlib.Path.exists', return_value=True)
    async def test_interactive_commit_basic(self, mock_path_exists, mock_which, mock_input):
        # Arrange
        mock_input.side_effect = ['feat', 'cli', 'Add new commit command', '', 'n', 'y']
        args = argparse.Namespace(
            message=None,
            run_tests=False,
            project_dir=Path('.'),
            generate=False,
            yes=False,
            agent="gemini",
            model=None
        )

        # Act
        with self.assertRaises(SystemExit) as cm:
            await run_commit(args)

        # Assert
        self.assertEqual(cm.exception.code, 0)
        expected_message = "feat(cli): Add new commit command"

        # Check that subprocess.run was called with the correct git commit command
        commit_call_found = False
        for call_args in self.mock_subprocess_run.call_args_list:
            command_list = call_args.args[0]
            if 'commit' in command_list:
                self.assertIn(expected_message, command_list)
                commit_call_found = True
                break
        self.assertTrue(commit_call_found, "git commit command was not called")

    @patch('builtins.input')
    @patch('shutil.which', return_value='/usr/bin/git')
    @patch('pathlib.Path.exists', return_value=True)
    async def test_non_interactive_commit(self, mock_path_exists, mock_which, mock_input):
        # Arrange
        commit_message = "feat: a regular commit"
        args = argparse.Namespace(
            message=commit_message,
            run_tests=False,
            project_dir=Path('.'),
            generate=False,
            yes=False,
            agent="gemini",
            model=None
        )

        # Act
        with self.assertRaises(SystemExit) as cm:
            await run_commit(args)

        # Assert
        self.assertEqual(cm.exception.code, 0)
        mock_input.assert_not_called()

        # Check that subprocess.run was called with the correct git commit command
        commit_call_found = False
        for call_args in self.mock_subprocess_run.call_args_list:
            command_list = call_args.args[0]
            if 'commit' in command_list:
                self.assertIn(commit_message, command_list)
                commit_call_found = True
                break
        self.assertTrue(commit_call_found, "git commit command was not called")

if __name__ == '__main__':
    unittest.main()
