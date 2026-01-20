import unittest
import shutil
import tempfile
import sys
from pathlib import Path
from unittest.mock import patch
from shared.cli_utils import _run_history_graph_logic

class TestHistoryGraph(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.history_file = self.test_dir / ".agent_history"

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_no_history(self):
        output = _run_history_graph_logic(self.test_dir)
        self.assertEqual(output, "No agent history found.")

    def test_empty_history(self):
        self.history_file.touch()
        output = _run_history_graph_logic(self.test_dir)
        self.assertEqual(output, "History is empty.")

    def test_single_run_tokens(self):
        run_id = "test-run-1"
        self.history_file.write_text(f"{run_id}\n")

        # Create metrics file
        metrics_file = self.test_dir / "final_metrics.txt"
        metrics_file.write_text(f"Run ID: {run_id}\nLLM Tokens Used: 1000\n")

        output = _run_history_graph_logic(self.test_dir, metric="tokens")
        self.assertIn("History: LLM Tokens Used", output)
        self.assertIn("run-1", output) # Label based on last 6 chars
        self.assertIn("1000.0", output)

    def test_multiple_runs_duration(self):
        run_id_1 = "test-run-1"
        run_id_2 = "test-run-2"
        self.history_file.write_text(f"{run_id_1}\n{run_id_2}\n")

        # Mock finding metrics files for different runs
        # Since _find_metrics_file searches specific locations, we can simulate by
        # putting files in archives.

        archive_1 = self.test_dir / ".agent_archives/run1"
        archive_1.mkdir(parents=True)
        (archive_1 / "final_metrics.txt").write_text(f"Run ID: {run_id_1}\nTotal Execution Time (s): 60\n")

        metrics_file_2 = self.test_dir / "final_metrics.txt"
        metrics_file_2.write_text(f"Run ID: {run_id_2}\nTotal Execution Time (s): 120\n")

        output = _run_history_graph_logic(self.test_dir, metric="duration")
        self.assertIn("History: Execution Time (s)", output)
        self.assertIn("60.0", output)
        self.assertIn("120.0", output)
        self.assertIn("run-1", output)
        self.assertIn("run-2", output)

if __name__ == '__main__':
    unittest.main()
