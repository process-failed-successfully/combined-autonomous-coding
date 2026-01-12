import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import argparse
import sys
import io

# Add project root to path to allow direct import of main
sys.path.insert(0, str(Path(__file__).parent.parent))

import main
from shared.cli_utils import _run_next_logic

class TestNextCommand(unittest.TestCase):

    def setUp(self):
        # Create a dummy project directory for tests
        self.project_dir = Path("/tmp/test_project")
        self.project_dir.mkdir(exist_ok=True)

    def tearDown(self):
        # Clean up the dummy directory
        import shutil
        shutil.rmtree(self.project_dir)

    @patch('shared.cli_utils.get_suggestions')
    def test_next_command_no_suggestions(self, mock_get_suggestions):
        """Test the 'next' command when there are no suggestions."""
        mock_get_suggestions.return_value = []

        args = argparse.Namespace(project_dir=self.project_dir, yes=False)

        # Redirect stdout to capture output
        captured_output = io.StringIO()
        sys.stdout = captured_output

        with self.assertRaises(SystemExit) as cm:
            main.run_next(args)

        sys.stdout = sys.__stdout__  # Restore stdout

        self.assertEqual(cm.exception.code, 0)
        output = captured_output.getvalue()
        self.assertIn("Project is in a clean state", output)

    @patch('main.run_commit')
    @patch('builtins.input', return_value='y')
    @patch('shared.cli_utils._has_uncommitted_changes', return_value=True)
    @patch('shared.cli_utils.get_workflow_stage', return_value="IN_PROGRESS")
    def test_next_command_suggests_commit_and_user_confirms(self, mock_stage, mock_changes, mock_input, mock_run_commit):
        """Test suggesting 'commit' and executing after user confirmation."""
        args = argparse.Namespace(project_dir=self.project_dir, yes=False)

        # Mock the SystemExit from run_commit
        mock_run_commit.side_effect = SystemExit(0)

        with self.assertRaises(SystemExit) as cm:
            main.run_next(args)

        self.assertEqual(cm.exception.code, 0)
        mock_run_commit.assert_called_once()
        # Check that the arguments passed to run_commit are as expected
        called_args = mock_run_commit.call_args[0][0]
        self.assertEqual(called_args.command, 'commit')

    @patch('main.run_workflow')
    @patch('builtins.input', return_value='y')
    @patch('shared.cli_utils._has_uncommitted_changes', return_value=False)
    @patch('shared.cli_utils.get_workflow_stage', return_value="COMPLETED")
    def test_next_command_suggests_workflow_and_user_confirms(self, mock_stage, mock_changes, mock_input, mock_run_workflow):
        """Test suggesting 'workflow advance' and executing after user confirmation."""
        # Create the COMPLETED file to be found by get_suggestions
        (self.project_dir / "COMPLETED").touch()

        args = argparse.Namespace(project_dir=self.project_dir, yes=False)

        # Mock the SystemExit from run_workflow
        mock_run_workflow.side_effect = SystemExit(0)

        with self.assertRaises(SystemExit) as cm:
            main.run_next(args)

        self.assertEqual(cm.exception.code, 0)
        mock_run_workflow.assert_called_once()
        called_args = mock_run_workflow.call_args[0][0]
        self.assertEqual(called_args.command, 'workflow')
        self.assertEqual(called_args.action, 'advance')

    @patch('main.run_commit')
    @patch('builtins.input', return_value='n')
    @patch('shared.cli_utils._has_uncommitted_changes', return_value=True)
    def test_next_command_user_declines(self, mock_changes, mock_input, mock_run_commit):
        """Test that the command is not executed if the user declines."""
        args = argparse.Namespace(project_dir=self.project_dir, yes=False)

        captured_output = io.StringIO()
        sys.stdout = captured_output

        with self.assertRaises(SystemExit) as cm:
            main.run_next(args)

        sys.stdout = sys.__stdout__

        self.assertEqual(cm.exception.code, 0)
        mock_run_commit.assert_not_called()
        self.assertIn("Aborted", captured_output.getvalue())

    @patch('main.run_commit')
    @patch('builtins.input')
    @patch('shared.cli_utils._has_uncommitted_changes', return_value=True)
    def test_next_command_with_yes_flag(self, mock_changes, mock_input, mock_run_commit):
        """Test that the command executes without a prompt with the --yes flag."""
        args = argparse.Namespace(project_dir=self.project_dir, yes=True)

        mock_run_commit.side_effect = SystemExit(0)

        with self.assertRaises(SystemExit) as cm:
            main.run_next(args)

        self.assertEqual(cm.exception.code, 0)
        mock_input.assert_not_called() # Ensure input() was not called
        mock_run_commit.assert_called_once()


if __name__ == '__main__':
    unittest.main()
