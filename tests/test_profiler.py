import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import tempfile
import sys
from shared.profiler import ProfilerManager

class TestProfilerManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temp_dir.name)
        self.manager = ProfilerManager(self.project_dir)
        # Mock console to avoid spamming stdout
        self.manager.console = MagicMock()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_run_success(self):
        # Create a dummy script
        script_path = self.project_dir / "test_script.py"
        script_path.write_text("print('Hello World')")

        success = self.manager.run(script_path, [])
        self.assertTrue(success)
        self.assertTrue(self.manager.stats_file.exists())
        self.assertGreater(self.manager.stats_file.stat().st_size, 0)

    def test_run_failure(self):
        # Script that doesn't exist
        script_path = self.project_dir / "non_existent.py"
        success = self.manager.run(script_path, [])
        self.assertFalse(success)

    def test_report_no_stats(self):
        self.manager.report()
        # Should print error to console
        # Note: rich markup formatting might make exact string matching tricky if logic changes,
        # but here we check if called.
        self.assertTrue(self.manager.console.print.called)
        args, _ = self.manager.console.print.call_args
        self.assertIn("not found", args[0])

    def test_report_success(self):
        # Create a dummy script and run it to generate stats
        script_path = self.project_dir / "test_script.py"
        script_path.write_text("x = sum(range(1000))")
        self.manager.run(script_path, [])

        # Now run report
        self.manager.report()
        # Should print a table
        # We verify that console.print was called with a Table object
        calls = self.manager.console.print.call_args_list
        # The last call should be the table (or error if something went wrong)
        from rich.table import Table
        # Check if any call arg was a Table
        found_table = False
        for call in calls:
            if isinstance(call[0][0], Table):
                found_table = True
                break
        self.assertTrue(found_table, "Report did not print a Table")

if __name__ == "__main__":
    unittest.main()
