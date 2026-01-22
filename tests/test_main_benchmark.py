from main import (
    _find_metrics_file,
    _parse_metrics,
    _benchmark_show,
    _benchmark_compare,
    _benchmark_summary,
)
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import io
import sys

# Add the project root to the Python path to allow importing from 'main'
sys.path.insert(0, str(Path(__file__).parent.parent))


METRICS_CONTENT_1 = """Run ID: test-run-1
Agent Type: gemini
Model: gemini-1.5-pro
Timestamp: 2023-01-01 12:00:00
Total Execution Time (s): 120.5
Total Iterations: 10
Total Errors: 1
LLM API Calls: 25
LLM Tokens Used: 15000
"""

METRICS_CONTENT_2 = """Run ID: test-run-2
Agent Type: cursor
Model: claude-3-5-sonnet
Timestamp: 2023-01-02 14:30:00
Total Execution Time (s): 95.2
Total Iterations: 8
Total Errors: 0
LLM API Calls: 20
LLM Tokens Used: 12500
"""

METRICS_CONTENT_3 = """Run ID: test-run-3
Agent Type: gemini
Model: gemini-1.5-pro
Timestamp: 2023-01-03 18:00:00
Total Execution Time (s): 150.0
Total Iterations: 12
Total Errors: 2
LLM API Calls: 30
LLM Tokens Used: 20000
"""

METRICS_CONTENT_4_ERRORS_DOWN = """Run ID: test-run-4
Agent Type: gemini
Model: gemini-1.5-pro
Total Errors: 0
"""

METRICS_CONTENT_5_ERRORS_UP = """Run ID: test-run-5
Agent Type: gemini
Model: gemini-1.5-pro
Total Errors: 3
"""


class TestBenchmarkCommand(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_find_metrics_file_in_project_dir(self):
        metrics_file = self.project_dir / "final_metrics.txt"
        metrics_file.write_text(METRICS_CONTENT_1)
        found_file = _find_metrics_file("test-run-1", self.project_dir)
        self.assertEqual(found_file, metrics_file)

    def test_find_metrics_file_in_archives(self):
        archive_dir = self.project_dir / ".agent_archives" / "archive-1"
        archive_dir.mkdir(parents=True)
        metrics_file = archive_dir / "final_metrics.txt"
        metrics_file.write_text(METRICS_CONTENT_2)
        found_file = _find_metrics_file("test-run-2", self.project_dir)
        self.assertEqual(found_file, metrics_file)

    def test_find_metrics_file_in_trash(self):
        trash_dir = self.project_dir / ".agent_trash" / "trash-1"
        trash_dir.mkdir(parents=True)
        metrics_file = trash_dir / "final_metrics.txt"
        metrics_file.write_text(METRICS_CONTENT_3)
        found_file = _find_metrics_file("test-run-3", self.project_dir)
        self.assertEqual(found_file, metrics_file)

    def test_find_metrics_file_not_found(self):
        found_file = _find_metrics_file("non-existent-run", self.project_dir)
        self.assertIsNone(found_file)

    def test_parse_metrics(self):
        metrics_file = self.project_dir / "final_metrics.txt"
        metrics_file.write_text(METRICS_CONTENT_1)
        metrics = _parse_metrics(metrics_file)
        self.assertEqual(metrics["Run ID"], "test-run-1")
        self.assertEqual(metrics["Total Execution Time (s)"], 120.5)
        self.assertEqual(metrics["Total Iterations"], 10)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_benchmark_show_specific_run(self, mock_stdout):
        # Setup mock file system
        archive_dir = self.project_dir / ".agent_archives" / "archive-1"
        archive_dir.mkdir(parents=True)
        (archive_dir / "final_metrics.txt").write_text(METRICS_CONTENT_1)

        args = MagicMock(run_id="test-run-1", project_dir=self.project_dir)
        with self.assertRaises(SystemExit) as cm:
            _benchmark_show(args)
        self.assertEqual(cm.exception.code, 0)

        output = mock_stdout.getvalue()
        self.assertIn("--- Metrics for Run: test-run-1 ---", output)
        self.assertIn("Total Execution Time (s) : 2m 0.50s", output)
        self.assertIn("Total Iterations         : 10", output)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_benchmark_show_latest_run(self, mock_stdout):
        (self.project_dir / "final_metrics.txt").write_text(METRICS_CONTENT_2)

        args = MagicMock(run_id=None, project_dir=self.project_dir)
        with self.assertRaises(SystemExit) as cm:
            _benchmark_show(args)
        self.assertEqual(cm.exception.code, 0)

        output = mock_stdout.getvalue()
        self.assertIn("--- Metrics for Run: test-run-2 ---", output)
        self.assertIn("Agent Type               : cursor", output)
        self.assertIn("Total Execution Time (s) : 1m 35.20s", output)

    @patch('sys.stderr', new_callable=io.StringIO)
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_benchmark_show_not_found(self, mock_stdout, mock_stderr):
        args = MagicMock(run_id="non-existent", project_dir=self.project_dir)
        with self.assertRaises(SystemExit) as cm:
            _benchmark_show(args)
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("Error: Could not find metrics for Run ID: non-existent", mock_stderr.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_benchmark_compare(self, mock_stdout):
        # Setup mock file system
        archive1 = self.project_dir / ".agent_archives" / "archive-1"
        archive1.mkdir(parents=True)
        (archive1 / "final_metrics.txt").write_text(METRICS_CONTENT_1)

        archive2 = self.project_dir / ".agent_archives" / "archive-2"
        archive2.mkdir(parents=True)
        (archive2 / "final_metrics.txt").write_text(METRICS_CONTENT_2)

        args = MagicMock(run_id_1="test-run-1", run_id_2="test-run-2", project_dir=self.project_dir)
        with self.assertRaises(SystemExit) as cm:
            _benchmark_compare(args)
        self.assertEqual(cm.exception.code, 0)

        output = mock_stdout.getvalue()
        self.assertIn("--- Comparison: test-run-1 vs test-run-2 ---", output)
        self.assertIn("Total Execution Time (s)", output)
        self.assertIn("2m 0.50s", output)  # value for run 1
        self.assertIn("1m 35.20s", output)  # value for run 2
        self.assertIn("✅ 0m 25.30s", output)  # Difference

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_benchmark_compare_error_metric(self, mock_stdout):
        # Test case where errors decrease (improvement)
        archive1 = self.project_dir / ".agent_archives" / "archive-1"
        archive1.mkdir(parents=True)
        (archive1 / "final_metrics.txt").write_text(METRICS_CONTENT_1)  # 1 error

        archive4 = self.project_dir / ".agent_archives" / "archive-4"
        archive4.mkdir(parents=True)
        (archive4 / "final_metrics.txt").write_text(METRICS_CONTENT_4_ERRORS_DOWN)  # 0 errors

        args = MagicMock(run_id_1="test-run-1", run_id_2="test-run-4", project_dir=self.project_dir)
        with self.assertRaises(SystemExit):
            _benchmark_compare(args)

        output = mock_stdout.getvalue()
        self.assertIn("Total Errors", output)
        self.assertIn("✅ -1.00", output)

        # Test case where errors increase (regression)
        mock_stdout.truncate(0)
        mock_stdout.seek(0)

        archive5 = self.project_dir / ".agent_archives" / "archive-5"
        archive5.mkdir(parents=True)
        (archive5 / "final_metrics.txt").write_text(METRICS_CONTENT_5_ERRORS_UP)  # 3 errors

        args = MagicMock(run_id_1="test-run-1", run_id_2="test-run-5", project_dir=self.project_dir)
        with self.assertRaises(SystemExit):
            _benchmark_compare(args)

        output = mock_stdout.getvalue()
        self.assertIn("Total Errors", output)
        self.assertIn("🔻 +2.00", output)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_benchmark_summary(self, mock_stdout):
        # Setup history and metrics files
        (self.project_dir / ".agent_history").write_text("test-run-1\ntest-run-2\ntest-run-3\n")

        archive1 = self.project_dir / ".agent_archives" / "archive-1"
        archive1.mkdir(parents=True)
        (archive1 / "final_metrics.txt").write_text(METRICS_CONTENT_1)

        archive2 = self.project_dir / ".agent_archives" / "archive-2"
        archive2.mkdir(parents=True)
        (archive2 / "final_metrics.txt").write_text(METRICS_CONTENT_2)

        (self.project_dir / "final_metrics.txt").write_text(METRICS_CONTENT_3)

        args = MagicMock(count=5, project_dir=self.project_dir)
        with self.assertRaises(SystemExit) as cm:
            _benchmark_summary(args)
        self.assertEqual(cm.exception.code, 0)

        output = mock_stdout.getvalue()
        self.assertIn("--- Metrics Summary (Last 5 Runs) ---", output)
        self.assertIn("test-run-3", output)
        self.assertIn("test-run-2", output)
        self.assertIn("test-run-1", output)
        self.assertIn("2m 30.00s", output)  # Time for run 3
        self.assertIn("12", output)  # Iterations for run 3


if __name__ == '__main__':
    unittest.main()
