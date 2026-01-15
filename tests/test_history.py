
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import os

# Add the root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import run_history

class TestHistoryCommand(unittest.TestCase):

    def setUp(self):
        self.project_dir = Path("test_project")
        self.project_dir.mkdir(exist_ok=True)
        self.history_file = self.project_dir / ".agent_history"

    def tearDown(self):
        if self.history_file.exists():
            self.history_file.unlink()
        if self.project_dir.exists():
            self.project_dir.rmdir()

    @patch('main._run_history_logic')
    @patch('sys.exit')
    def test_run_history_summary(self, mock_exit, mock_history_logic):
        """Test the history command in summary view."""
        args = MagicMock()
        args.project_dir = self.project_dir
        args.run_id = None
        args.agent = None

        run_history(args)

        mock_history_logic.assert_called_once_with(
            project_dir=self.project_dir,
            run_id=None,
            agent_filter=None
        )
        mock_exit.assert_called_once_with(0)

    @patch('main._run_history_logic')
    @patch('sys.exit')
    def test_run_history_detailed_view(self, mock_exit, mock_history_logic):
        """Test the history command for a detailed view of a specific run."""
        args = MagicMock()
        args.project_dir = self.project_dir
        args.run_id = "test_run_id"
        args.agent = None

        run_history(args)

        mock_history_logic.assert_called_once_with(
            project_dir=self.project_dir,
            run_id="test_run_id",
            agent_filter=None
        )
        mock_exit.assert_called_once_with(0)

    @patch('main._run_history_logic')
    @patch('sys.exit')
    def test_run_history_with_agent_filter(self, mock_exit, mock_history_logic):
        """Test the history command with an agent filter."""
        args = MagicMock()
        args.project_dir = self.project_dir
        args.run_id = None
        args.agent = "gemini"

        run_history(args)

        mock_history_logic.assert_called_once_with(
            project_dir=self.project_dir,
            run_id=None,
            agent_filter="gemini"
        )
        mock_exit.assert_called_once_with(0)

if __name__ == '__main__':
    unittest.main()
