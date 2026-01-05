import unittest
import tempfile
import shutil
from pathlib import Path
import io
from argparse import Namespace
from unittest.mock import patch

# Import the main module to be tested
import main

class TestMainHistory(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory structure for each test."""
        self.test_dir = tempfile.mkdtemp()
        self.test_dir_path = Path(self.test_dir)
        self.project_dir = self.test_dir_path / "my_test_project"
        self.project_dir.mkdir()
        self.repo_root = self.test_dir_path / "repo"
        self.logs_dir = self.repo_root / "agents" / "logs"
        self.logs_dir.mkdir(parents=True)
        self.main_py_path = self.repo_root / "main.py"
        self.maxDiff = None

    def tearDown(self):
        """Clean up the temporary directory after each test."""
        shutil.rmtree(self.test_dir)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_history_no_history_file(self, mock_stdout):
        """Test that the command exits gracefully when no .agent_history file is found."""
        with patch('main.__file__', str(self.main_py_path)):
            args = Namespace(project_dir=self.project_dir)
            with self.assertRaises(SystemExit) as cm:
                main.run_history(args)
            self.assertEqual(cm.exception.code, 0)
            self.assertIn("No agent run history found for this project", mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_history_with_valid_logs(self, mock_stdout):
        """Test the happy path with an existing history file and all corresponding log files."""
        with patch('main.__file__', str(self.main_py_path)):
            args = Namespace(project_dir=self.project_dir)

            (self.project_dir / ".agent_history").write_text("run-001\nrun-002\n")
            (self.logs_dir / "run-001.log").write_text("2024-01-01 10:00:00,000 - INFO - Start of run 1\nrun 1 complete")
            (self.logs_dir / "run-002.log").write_text("2024-01-02 11:00:00,000 - INFO - Start of run 2\nrun 2 complete")

            with self.assertRaises(SystemExit) as cm:
                main.run_history(args)
            self.assertEqual(cm.exception.code, 0)

            output = mock_stdout.getvalue()
            self.assertIn(f"--- Agent Run History: {self.project_dir.resolve()} ---", output)
            self.assertIn("[2] Run ID: run-002 (latest)", output)
            self.assertIn("Timestamp: 2024-01-02 11:00:00,000", output)
            self.assertIn("run 2 complete", output)
            self.assertIn("[1] Run ID: run-001", output)
            self.assertIn("Timestamp: 2024-01-01 10:00:00,000", output)
            self.assertIn("run 1 complete", output)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_history_with_missing_log(self, mock_stdout):
        """Test that the command handles a missing log file gracefully."""
        with patch('main.__file__', str(self.main_py_path)):
            args = Namespace(project_dir=self.project_dir)
            (self.project_dir / ".agent_history").write_text("run-001\nrun-MISSING\n")
            (self.logs_dir / "run-001.log").write_text("2024-01-01 10:00:00,000 - INFO - Start of run 1\nrun 1 complete")

            with self.assertRaises(SystemExit) as cm:
                main.run_history(args)
            self.assertEqual(cm.exception.code, 0)

            output = mock_stdout.getvalue()
            self.assertIn(f"--- Agent Run History: {self.project_dir.resolve()} ---", output)
            self.assertIn("[2] Run ID: run-MISSING (latest)", output)
            self.assertIn("Log file not found", output)
            self.assertIn("[1] Run ID: run-001", output)
            self.assertIn("Timestamp: 2024-01-01 10:00:00,000", output)
            self.assertIn("run 1 complete", output)

if __name__ == "__main__":
    unittest.main()
