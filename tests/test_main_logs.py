import unittest
from unittest.mock import patch, MagicMock, mock_open
import argparse
from pathlib import Path
import main

class TestMainLogs(unittest.TestCase):

    @patch('main.Path')
    def test_run_logs_no_logs_dir(self, mock_Path_class):
        mock_repo_root = MagicMock(spec=Path)
        mock_logs_dir = MagicMock(spec=Path)
        mock_Path_class.return_value.parent = mock_repo_root
        mock_repo_root.__truediv__.return_value = mock_logs_dir
        mock_logs_dir.exists.return_value = False

        args = argparse.Namespace(run_id=None)

        with self.assertRaises(SystemExit) as cm:
            with patch('builtins.print') as mock_print:
                main.run_logs(args)

        self.assertEqual(cm.exception.code, 1)
        mock_print.assert_any_call("Logs directory not found.")

    @patch('main.Path')
    @patch('builtins.print')
    def test_run_logs_no_logs_found(self, mock_print, mock_Path_class):
        mock_repo_root = MagicMock(spec=Path)
        mock_logs_dir = MagicMock(spec=Path)
        mock_Path_class.return_value.parent = mock_repo_root
        mock_repo_root.__truediv__.return_value = mock_logs_dir
        mock_logs_dir.exists.return_value = True
        mock_logs_dir.glob.return_value = []

        args = argparse.Namespace(run_id=None)

        with self.assertRaises(SystemExit) as cm:
            main.run_logs(args)

        self.assertEqual(cm.exception.code, 0)
        mock_print.assert_any_call("No logs found.")

    @patch('main.Path')
    def test_run_logs_list_logs(self, mock_Path_class):
        mock_repo_root = MagicMock(spec=Path)
        mock_logs_dir = MagicMock(spec=Path)
        mock_Path_class.return_value.parent = mock_repo_root
        mock_repo_root.__truediv__.return_value = mock_logs_dir
        mock_logs_dir.exists.return_value = True

        # Create mock log files
        log1 = MagicMock(spec=Path); log1.stem = 'log1'; log1.stat.return_value.st_mtime = 1
        log2 = MagicMock(spec=Path); log2.stem = 'log2'; log2.stat.return_value.st_mtime = 2
        log3 = MagicMock(spec=Path); log3.stem = 'log3'; log3.stat.return_value.st_mtime = 3

        # Return them in a non-sorted order
        mock_logs_dir.glob.return_value = [log2, log1, log3]

        args = argparse.Namespace(run_id=None)

        with patch('builtins.print') as mock_print:
            with self.assertRaises(SystemExit) as cm:
                main.run_logs(args)

        self.assertEqual(cm.exception.code, 0)
        mock_print.assert_any_call("--- Last 10 Agent Logs ---")
        calls = mock_print.call_args_list
        # The sorted order should be log3, log2, log1
        self.assertEqual(calls[1].args[0], "  - log3 (latest)")
        self.assertEqual(calls[2].args[0], "  - log2")
        self.assertEqual(calls[3].args[0], "  - log1")

    @patch('main.Path')
    def test_run_logs_view_log_not_found(self, mock_Path_class):
        mock_repo_root = MagicMock(spec=Path)
        mock_logs_dir = MagicMock(spec=Path)
        mock_log_file = MagicMock(spec=Path)
        mock_Path_class.return_value.parent = mock_repo_root
        mock_repo_root.__truediv__.return_value = mock_logs_dir
        mock_logs_dir.exists.return_value = True
        mock_logs_dir.__truediv__.return_value = mock_log_file
        mock_log_file.exists.return_value = False

        args = argparse.Namespace(run_id='test_log')

        with self.assertRaises(SystemExit) as cm:
            with patch('builtins.print') as mock_print:
                main.run_logs(args)

        self.assertEqual(cm.exception.code, 1)
        mock_print.assert_any_call("Log file not found for Run ID: test_log")

    @patch('main.Path')
    @patch('builtins.open', new_callable=mock_open, read_data="Log content")
    def test_run_logs_view_log_success(self, mock_open_file, mock_Path_class):
        mock_repo_root = MagicMock(spec=Path)
        mock_logs_dir = MagicMock(spec=Path)
        mock_log_file = MagicMock(spec=Path)
        mock_Path_class.return_value.parent = mock_repo_root
        mock_repo_root.__truediv__.return_value = mock_logs_dir
        mock_logs_dir.exists.return_value = True
        mock_logs_dir.__truediv__.return_value = mock_log_file
        mock_log_file.exists.return_value = True

        args = argparse.Namespace(run_id='test_log')

        with patch('builtins.print') as mock_print:
            with self.assertRaises(SystemExit) as cm:
                main.run_logs(args)

        self.assertEqual(cm.exception.code, 0)
        mock_open_file.assert_called_with(mock_log_file, 'r', encoding='utf-8', errors='ignore')
        mock_print.assert_called_with("Log content")

if __name__ == '__main__':
    unittest.main()
