import unittest
import argparse
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Import main correctly
sys.path.append(str(Path(__file__).parent.parent))
from main import run_todos

class TestTodosLabIntegration(unittest.TestCase):
    @patch('main.run_tui')
    def test_run_todos_tui(self, mock_run_tui):
        """
        Tests that calling run_todos with --tui properly delegates
        to the main TUI runner with the 'tab-todos' argument.
        """
        args = argparse.Namespace()
        args.tui = True
        args.project_dir = Path(".")
        args.tags = []
        args.exclude_paths = []

        # Execute
        run_todos(args)

        # Assert
        mock_run_tui.assert_called_once_with(args, start_tab="tab-todos")

    @patch('shared.todos.scan_todos')
    @patch('sys.stdout', new_callable=MagicMock)
    def test_run_todos_cli_no_todos(self, mock_stdout, mock_scan):
        """
        Tests that calling run_todos without --tui runs the standard
        CLI scan functionality.
        """
        args = argparse.Namespace()
        args.tui = False
        args.project_dir = Path(".")
        args.tags = []
        args.exclude_paths = []
        args.json = False
        args.blame = False

        mock_scan.return_value = []

        # Execute
        with self.assertRaises(SystemExit) as cm:
            run_todos(args)

        self.assertEqual(cm.exception.code, 0)

        # Assert
        mock_scan.assert_called_once_with(Path(".").resolve(), tags=None)

if __name__ == '__main__':
    unittest.main()
