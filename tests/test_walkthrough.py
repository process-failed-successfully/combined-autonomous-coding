import unittest
from unittest.mock import patch, MagicMock, ANY
from io import StringIO
from pathlib import Path
import sys
import os

# Add the root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import run_walkthrough

class TestWalkthrough(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path("test_project_dir_walkthrough")
        self.test_dir.mkdir(exist_ok=True)

    def tearDown(self):
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    @patch('main.run_init')
    @patch('builtins.input', side_effect=['1', 'q'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_new_project_state_and_action(self, mock_stdout, mock_input, mock_run_init):
        args = MagicMock(project_dir=self.test_dir)

        # Simulate a new project (no git repo)
        with patch('pathlib.Path.is_dir', return_value=False):
            with self.assertRaises(SystemExit):
                run_walkthrough(args)

        output = mock_stdout.getvalue()
        self.assertIn("Looks like this is a new project.", output)
        self.assertIn("[1] Initialize the project", output)
        mock_run_init.assert_called_once()

    @patch('builtins.input', side_effect=['q'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_initialized_no_spec_state(self, mock_stdout, mock_input):
        args = MagicMock(project_dir=self.test_dir)

        # Simulate an initialized project (git repo exists) but no spec file
        with patch('pathlib.Path.is_dir', return_value=True):
            with patch('pathlib.Path.exists', return_value=False):
                with self.assertRaises(SystemExit):
                    run_walkthrough(args)

        output = mock_stdout.getvalue()
        self.assertIn("Project is initialized, but no 'app_spec.txt' found.", output)
        self.assertIn("[1] Initialize to create a spec file", output)

    @patch('builtins.input', side_effect=['q'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_has_spec_state(self, mock_stdout, mock_input):
        args = MagicMock(project_dir=self.test_dir)

        # Simulate a project with a spec file
        with patch('pathlib.Path.is_dir', return_value=True):
            def exists_side_effect(instance):
                return instance.name == 'app_spec.txt'
            with patch('pathlib.Path.exists', side_effect=exists_side_effect, autospec=True):
                with self.assertRaises(SystemExit):
                    run_walkthrough(args)

        output = mock_stdout.getvalue()
        self.assertIn("Project has a specification.", output)
        self.assertIn("[1] Run agent to work on the project", output)
        self.assertIn("[2] Generate a plan without running the agent", output)

    @patch('main.run_review')
    @patch('builtins.input', side_effect=['1', 'q'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_completed_state_and_action(self, mock_stdout, mock_input, mock_run_review):
        args = MagicMock(project_dir=self.test_dir)

        # Simulate a project that is marked as complete
        with patch('pathlib.Path.is_dir', return_value=True):
            def exists_side_effect(instance):
                return instance.name in ['app_spec.txt', 'COMPLETED']
            with patch('pathlib.Path.exists', side_effect=exists_side_effect, autospec=True):
                with self.assertRaises(SystemExit):
                    run_walkthrough(args)

        output = mock_stdout.getvalue()
        self.assertIn("Agent has marked work as complete.", output)
        self.assertIn("[1] Start interactive QA review", output)
        mock_run_review.assert_called_once()

    @patch('builtins.input', side_effect=['q'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_qa_passed_state(self, mock_stdout, mock_input):
        args = MagicMock(project_dir=self.test_dir)

        # Simulate a project that has passed QA
        with patch('pathlib.Path.is_dir', return_value=True):
            def exists_side_effect(instance):
                return instance.name in ['app_spec.txt', 'COMPLETED', 'QA_PASSED']
            with patch('pathlib.Path.exists', side_effect=exists_side_effect, autospec=True):
                with self.assertRaises(SystemExit):
                    run_walkthrough(args)

        output = mock_stdout.getvalue()
        self.assertIn("Project has passed QA and is awaiting manager sign-off.", output)
        self.assertIn("[1] Run agent for manager sign-off", output)

    @patch('main.run_clean')
    @patch('builtins.input', side_effect=['1', 'q'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_signed_off_state_and_action(self, mock_stdout, mock_input, mock_run_clean):
        args = MagicMock(project_dir=self.test_dir)

        # Simulate a project that is signed off
        with patch('pathlib.Path.is_dir', return_value=True):
            def exists_side_effect(instance):
                return instance.name in ['app_spec.txt', 'COMPLETED', 'QA_PASSED', 'PROJECT_SIGNED_OFF']
            with patch('pathlib.Path.exists', side_effect=exists_side_effect, autospec=True):
                with self.assertRaises(SystemExit):
                    run_walkthrough(args)

        output = mock_stdout.getvalue()
        self.assertIn("Project is signed off and complete!", output)
        self.assertIn("[1] Clean up project artifacts", output)
        mock_run_clean.assert_called_once()

if __name__ == '__main__':
    unittest.main()
