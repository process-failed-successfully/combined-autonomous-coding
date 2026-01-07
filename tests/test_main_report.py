
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import shutil
from datetime import datetime, timezone
import io
from contextlib import redirect_stdout

# Make sure the main script can be imported
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from main import parse_args, run_report
from shared.cli_utils import _run_report_logic

class TestMainReportCommand(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir) / "project"
        self.project_dir.mkdir()

        (self.project_dir / ".git").mkdir()

        self.logs_dir = Path(self.test_dir) / "agents/logs"
        self.logs_dir.mkdir(parents=True)

        self.run_id = "test-run-12345"
        self.log_file_path = self.logs_dir / f"{self.run_id}.log"
        self.metrics_file_path = self.project_dir / "final_metrics.txt"

        start_time = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        end_time = datetime(2023, 1, 1, 12, 30, 0, tzinfo=timezone.utc)

        self.log_file_path.write_text(
            f"{start_time.isoformat()} - INFO - Agent started\n"
            f"...\n"
            f"2023-01-01T12:15:00+00:00 - INFO - Git commit: abc1234\n"
            f"{end_time.isoformat()} - INFO - Agent finished\n"
        )
        self.metrics_file_path.write_text(
            "Run ID: test-run-12345\n"
            "Total Execution Time (s): 1800.0\n"
            "Total Iterations: 5\n"
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('subprocess.run')
    @patch('shutil.which', return_value='/usr/bin/git')
    def test_run_report_logic_success(self, mock_which, mock_subprocess_run):
        # This test now calls the logic function directly to avoid patching __file__

        # Arrange
        mock_subprocess_run.return_value = MagicMock(
            returncode=0,
            stdout="commit abc1234\nAuthor: Test\nDate: Test\n\n    Test commit\n\n 1 file changed, 1 insertion(+)"
        )

        f = io.StringIO()
        with redirect_stdout(f):
            success = _run_report_logic(
                run_id=self.run_id,
                output_path=None,
                project_dir=self.project_dir,
                repo_root_for_test=Path(self.test_dir)
            )

        # Assert
        self.assertTrue(success)
        output = f.getvalue()
        self.assertIn("# Agent Run Report: test-run-12345", output)
        self.assertIn("## 📊 Summary", output)
        self.assertIn("| **Run ID** | `test-run-12345` |", output)
        self.assertIn("| **Total Time** | 30m 0.00s |", output)
        self.assertIn("## 💻 Code Changes", output)
        self.assertIn("Found commit associated with this run: `abc1234`", output)
        self.assertIn("1 file changed, 1 insertion(+)", output)
        self.assertIn("## 📝 Notable Log Events", output)
        self.assertIn("No specific high-priority events found in the log.", output)

    @patch('main.sys.exit')
    @patch('main._run_report_logic')
    def test_main_command_dispatch(self, mock_run_logic, mock_exit):
        # This test ensures that `main.py` correctly calls the logic function.

        # Arrange
        mock_run_logic.return_value = True

        # Act
        args = parse_args(['report', self.run_id, '--project-dir', str(self.project_dir)])
        run_report(args)

        # Assert
        mock_run_logic.assert_called_once_with(
            run_id=self.run_id,
            output_path=None,
            project_dir=self.project_dir
        )
        mock_exit.assert_called_with(0)
