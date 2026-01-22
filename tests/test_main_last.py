from main import _run_last_logic
import unittest
from unittest.mock import patch
from pathlib import Path
import tempfile
import shutil
import io
import contextlib

# Make sure the main module can be imported
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestLastCommand(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.temp_dir)
        self.repo_root = Path(__file__).resolve().parent.parent
        self.logs_dir = self.repo_root / "agents/logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        # Clean up logs created during tests
        for log_file in self.logs_dir.glob("test-run-*.log"):
            log_file.unlink()

    def test_run_last_logic_success(self):
        # --- Setup mock files ---
        # 1. History file
        history_file = self.project_dir / ".agent_history"
        history_file.write_text("old-run-id-123\nlast-run-id-456\n")

        # 2. Metrics file for the last run
        metrics_content = """Run ID: last-run-id-456
Total Execution Time (s): 123.45
Total Iterations: 5
Total Errors: 1
"""
        metrics_file = self.project_dir / "final_metrics.txt"
        metrics_file.write_text(metrics_content)

        # 3. QA summary file
        qa_summary_content = "QA Passed: All tests successful."
        qa_summary_file = self.project_dir / "qa_summary.txt"
        qa_summary_file.write_text(qa_summary_content)

        # 4. Log file
        log_content = "\n".join([f"Line {i}" for i in range(20)])
        log_file = self.logs_dir / "last-run-id-456.log"
        log_file.write_text(log_content)

        # --- Execute and Capture Output ---
        stdout_capture = io.StringIO()
        with contextlib.redirect_stdout(stdout_capture):
            # We need to patch the repo_root detection in the main module
            with patch('main.Path.parent', self.repo_root):
                result = _run_last_logic(self.project_dir)

        output = stdout_capture.getvalue()

        # --- Assertions ---
        self.assertTrue(result)
        self.assertTrue(output.startswith("--- Summary of Last Run:"))
        self.assertIn("Last Run ID: last-run-id-456", output)

        # Check for metrics
        self.assertIn("--- Performance Metrics ---", output)
        self.assertIn("Total Execution Time (s) : 2m 3.45s", output)  # Check formatting
        self.assertIn("Total Iterations         : 5", output)
        self.assertIn("Total Errors             : 1", output)

        # Check for QA summary
        self.assertIn("--- QA Summary ---", output)
        self.assertIn(qa_summary_content, output)

        # Check for log summary (last 10 lines)
        self.assertIn("--- Log Summary (Last 10 lines) ---", output)
        self.assertIn("Line 19", output)
        self.assertNotIn("Line 9", output)

    def test_run_last_no_history(self):
        stdout_capture = io.StringIO()
        with contextlib.redirect_stdout(stdout_capture):
            result = _run_last_logic(self.project_dir)
        output = stdout_capture.getvalue()

        self.assertFalse(result)
        self.assertIn("No agent run history found", output)

    def test_run_last_missing_files(self):
        # Setup history file, but nothing else
        history_file = self.project_dir / ".agent_history"
        history_file.write_text("only-run-id-789\n")

        stdout_capture = io.StringIO()
        with contextlib.redirect_stdout(stdout_capture):
            result = _run_last_logic(self.project_dir)
        output = stdout_capture.getvalue()

        self.assertTrue(result)
        self.assertIn("Last Run ID: only-run-id-789", output)
        self.assertIn("No metrics file found for the last run", output)
        self.assertIn("No QA summary found for the last run", output)
        self.assertIn("Log file not found", output)


if __name__ == '__main__':
    unittest.main()
