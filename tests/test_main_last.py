import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import os
import sys

# Add the root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import run_last

class TestMainLast(unittest.TestCase):

    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.project_dir.mkdir(exist_ok=True)
        self.run_id_file = self.project_dir / ".agent_run_id"
        self.metrics_file = self.project_dir / "final_metrics.txt"
        self.qa_file = self.project_dir / "qa_summary.txt"
        self.log_dir = Path(__file__).parent.parent / "agents/logs"
        self.log_dir.mkdir(exist_ok=True)
        self.log_file = None

    def tearDown(self):
        if self.run_id_file.exists():
            self.run_id_file.unlink()
        if self.metrics_file.exists():
            self.metrics_file.unlink()
        if self.qa_file.exists():
            self.qa_file.unlink()
        if self.log_file and self.log_file.exists():
            self.log_file.unlink()
        if self.project_dir.exists():
            self.project_dir.rmdir()

    def test_run_last_success(self):
        # Create dummy files
        run_id = "test-run-123"
        self.run_id_file.write_text(run_id)
        self.metrics_file.write_text("Total Iterations: 5")
        self.qa_file.write_text("All tests passed.")
        self.log_file = self.log_dir / f"{run_id}.log"
        self.log_file.write_text("Log line 1\nLog line 2")

        args = MagicMock()
        args.project_dir = self.project_dir

        with patch('sys.stdout') as mock_stdout:
            with self.assertRaises(SystemExit) as cm:
                run_last(args)
            self.assertEqual(cm.exception.code, 0)

        # Check the output
        output = "".join(call.args[0] for call in mock_stdout.write.call_args_list)
        self.assertIn(f"Run ID: {run_id}", output)
        self.assertIn("Total Iterations: 5", output)
        self.assertIn("All tests passed.", output)
        self.assertIn("Log line 2", output)

    def test_run_last_no_run_id_file(self):
        args = MagicMock()
        args.project_dir = self.project_dir

        with patch('sys.stdout') as mock_stdout:
            with self.assertRaises(SystemExit) as cm:
                run_last(args)
            self.assertEqual(cm.exception.code, 0)

        output = "".join(call.args[0] for call in mock_stdout.write.call_args_list)
        self.assertIn("No last run found", output)

    def test_run_last_missing_files(self):
        run_id = "test-run-456"
        self.run_id_file.write_text(run_id)

        args = MagicMock()
        args.project_dir = self.project_dir

        with patch('sys.stdout') as mock_stdout:
            with self.assertRaises(SystemExit) as cm:
                run_last(args)
            self.assertEqual(cm.exception.code, 0)

        output = "".join(call.args[0] for call in mock_stdout.write.call_args_list)
        self.assertIn(f"Run ID: {run_id}", output)
        self.assertIn("final_metrics.txt not found", output)
        self.assertIn("qa_summary.txt not found", output)
        self.assertIn(f"Log file not found for run ID {run_id}", output)

    def test_run_last_empty_files(self):
        run_id = "test-run-789"
        self.run_id_file.write_text(run_id)
        self.metrics_file.write_text("")
        self.qa_file.write_text("")
        self.log_file = self.log_dir / f"{run_id}.log"
        self.log_file.write_text("")

        args = MagicMock()
        args.project_dir = self.project_dir

        with patch('sys.stdout') as mock_stdout:
            with self.assertRaises(SystemExit) as cm:
                run_last(args)
            self.assertEqual(cm.exception.code, 0)

        output = "".join(call.args[0] for call in mock_stdout.write.call_args_list)
        self.assertIn(f"Run ID: {run_id}", output)
        self.assertIn("final_metrics.txt is empty", output)
        self.assertIn("qa_summary.txt is empty", output)
        self.assertIn("Log file is empty", output)

if __name__ == '__main__':
    unittest.main()
