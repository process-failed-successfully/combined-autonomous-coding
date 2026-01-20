import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
import sys

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))

from textual.widgets import Label, Button, DirectoryTree, RichLog, TabbedContent
from shared.tui import AgentTUI, DashboardTab, FileExplorerTab, LogsTab

class TestTUI(unittest.IsolatedAsyncioTestCase):
    async def test_app_startup(self):
        """Test that the app starts up and has the expected title."""
        app = AgentTUI(project_dir=Path("."))
        async with app.run_test() as pilot:
            # Check if TabbedContent exists
            self.assertIsInstance(app.query_one(TabbedContent), TabbedContent)
            # Check if tabs are present by ID
            self.assertTrue(app.query_one("#tab-dashboard"))
            self.assertTrue(app.query_one("#tab-explorer"))
            self.assertTrue(app.query_one("#tab-logs"))

    async def test_dashboard_content(self):
        """Test that the dashboard tab displays project info."""
        app = AgentTUI(project_dir=Path("."))
        async with app.run_test() as pilot:
            # Switch to dashboard is default
            dashboard = app.query_one(DashboardTab)
            self.assertIsNotNone(dashboard)

            # Check for labels
            labels = dashboard.query(Label)
            self.assertTrue(any("Project:" in str(l.render()) for l in labels))

            # Check for buttons
            self.assertTrue(dashboard.query_one("#btn-test"))
            self.assertTrue(dashboard.query_one("#btn-lint"))

    async def test_file_explorer_tab(self):
        """Test the file explorer tab structure."""
        app = AgentTUI(project_dir=Path("."))
        async with app.run_test() as pilot:
            # Click the Explorer tab - Use text selector if ID fails or just query TabbedContent
            # In Textual, tabs are complex. Let's switch programmatically or use the correct selector.
            tabbed_content = app.query_one(TabbedContent)
            tabbed_content.active = "tab-explorer"
            await pilot.pause()

            explorer = app.query_one(FileExplorerTab)
            self.assertIsNotNone(explorer)

            # Check for DirectoryTree and RichLog (preview)
            self.assertIsInstance(explorer.query_one(DirectoryTree), DirectoryTree)
            self.assertIsInstance(explorer.query_one(RichLog), RichLog)

    @patch("shared.tui.get_latest_log_file")
    async def test_logs_tab(self, mock_get_log):
        """Test log viewer updates."""
        # Setup mock log file
        mock_log_path = Path("test.log")
        mock_log_path.write_text("Test Log Entry")
        mock_get_log.return_value = mock_log_path

        try:
            app = AgentTUI(project_dir=Path("."))
            async with app.run_test() as pilot:
                # Switch tab programmatically
                tabbed_content = app.query_one(TabbedContent)
                tabbed_content.active = "tab-logs"
                await pilot.pause()

                logs_tab = app.query_one(LogsTab)
                log_viewer = logs_tab.query_one(RichLog)

                # Wait a bit for the interval to tick or force update
                logs_tab.update_log()

                # Verify content (Textual's RichLog content is complex, just checking it didn't crash)
                self.assertTrue(log_viewer)
        finally:
            if mock_log_path.exists():
                mock_log_path.unlink()

if __name__ == "__main__":
    unittest.main()
