import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import shutil
import tempfile

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))

from textual.widgets import Label, Button, ListView, RichLog, Input, Markdown
from shared.log_explorer import LogExplorerApp

class TestLogExplorerTUI(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.project_dir = self.test_dir / "project"
        self.project_dir.mkdir()

        # Create dummy logs
        self.log_file = self.project_dir / "test_run.log"
        self.log_file.write_text("INFO: Test Log Content\nERROR: Something went wrong")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch("shared.log_explorer.get_all_log_files")
    async def test_app_startup_and_load(self, mock_get_logs):
        """Test that the app starts up and loads logs."""
        mock_get_logs.return_value = [self.log_file]

        app = LogExplorerApp(project_dir=self.project_dir)
        async with app.run_test() as pilot:
            # Check widgets exist
            self.assertTrue(app.query_one("#log-list"))
            self.assertTrue(app.query_one("#log-viewer"))
            self.assertTrue(app.query_one("#log-filter"))

            # Check log list population
            log_list = app.query_one("#log-list", ListView)
            self.assertEqual(len(log_list.children), 1)

            # Check viewer content (it loads first log by default)
            viewer = app.query_one("#log-viewer", RichLog)
            # Accessing lines on RichLog is not direct, but we can assume it works if no error.
            # We can check app.current_log_path
            self.assertEqual(app.current_log_path, self.log_file)

    @patch("shared.log_explorer.get_all_log_files")
    async def test_filter(self, mock_get_logs):
        """Test the filter functionality."""
        mock_get_logs.return_value = [self.log_file]

        app = LogExplorerApp(project_dir=self.project_dir)
        async with app.run_test() as pilot:
            log_filter = app.query_one("#log-filter", Input)
            log_filter.value = "ERROR"

            # Wait for event processing
            await pilot.pause()

            # We can't easily inspect RichLog content in test without internal knowledge,
            # but we can verify no crash and current_log_path remains.
            self.assertEqual(app.current_log_path, self.log_file)

    @patch("shared.log_explorer.get_all_log_files")
    @patch("shared.log_explorer.run_ask_logic", new_callable=AsyncMock)
    async def test_analyze_button(self, mock_ask, mock_get_logs):
        """Test the analyze button."""
        mock_get_logs.return_value = [self.log_file]
        mock_ask.return_value = True # Success

        app = LogExplorerApp(project_dir=self.project_dir)
        async with app.run_test(size=(160, 40)) as pilot:
            # Click analyze
            btn = app.query_one("#btn-analyze")
            btn.focus()
            await pilot.press("enter")

            mock_ask.assert_called_once()

            # Check panel display
            panel = app.query_one("#analysis-panel")
            self.assertEqual(panel.styles.display, "block")

    @patch("shared.log_explorer.get_all_log_files")
    async def test_log_selection(self, mock_get_logs):
        """Test selecting a different log file."""
        log2 = self.project_dir / "test_run_2.log"
        log2.write_text("Log 2 Content")
        mock_get_logs.return_value = [self.log_file, log2]

        app = LogExplorerApp(project_dir=self.project_dir)
        async with app.run_test(size=(160, 40)) as pilot:
            log_list = app.query_one("#log-list", ListView)

            # Verify initial state
            self.assertEqual(app.current_log_path, self.log_file)

            # Simulate selection of second item
            # We can programmatically trigger the handler or use pilot
            # Using post_message to simulate the event is reliable
            item = log_list.children[1]
            log_list.post_message(ListView.Selected(log_list, item))

            await pilot.pause()

            self.assertEqual(app.current_log_path, log2)

if __name__ == "__main__":
    unittest.main()
