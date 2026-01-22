import main
import unittest
from pathlib import Path
import tempfile
import argparse
import io
from contextlib import redirect_stdout, redirect_stderr

# Add project root to path to allow direct import of main
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestLastRunId(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_last_run_id_success(self):
        """Test that the last run ID is correctly printed when the history file exists."""
        history_file = self.project_dir / ".agent_history"
        history_file.write_text("run-id-1\nrun-id-2\nrun-id-3\n")

        args = argparse.Namespace(project_dir=self.project_dir)

        f = io.StringIO()
        with redirect_stdout(f):
            with self.assertRaises(SystemExit) as cm:
                main.run_last_run_id(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertEqual(f.getvalue().strip(), "run-id-3")

    def test_last_run_id_empty_file(self):
        """Test that an error is shown when the history file is empty."""
        history_file = self.project_dir / ".agent_history"
        history_file.touch()

        args = argparse.Namespace(project_dir=self.project_dir)

        f_err = io.StringIO()
        with redirect_stderr(f_err):
            with self.assertRaises(SystemExit) as cm:
                main.run_last_run_id(args)

        self.assertEqual(cm.exception.code, 1)
        self.assertIn("History is empty", f_err.getvalue())

    def test_last_run_id_no_file(self):
        """Test that an error is shown when the history file does not exist."""
        args = argparse.Namespace(project_dir=self.project_dir)

        f_err = io.StringIO()
        with redirect_stderr(f_err):
            with self.assertRaises(SystemExit) as cm:
                main.run_last_run_id(args)

        self.assertEqual(cm.exception.code, 1)
        self.assertIn("No agent run history found", f_err.getvalue())


if __name__ == '__main__':
    unittest.main()
