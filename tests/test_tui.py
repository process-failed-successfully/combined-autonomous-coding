
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.tui import AgentTUI, HelpScreen, Dashboard, ProjectInfo

class TestTUI(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.project_dir = Path(".")

    async def test_show_help_screen(self):
        """Test that the help screen is displayed when 'h' is pressed."""
        app = AgentTUI(project_dir=self.project_dir)
        async with app.run_test() as pilot:
            await pilot.press("h")
            self.assertIsInstance(pilot.app.screen, HelpScreen)

    @patch('shared.tui.Dashboard.run_command')
    async def test_run_tests_action(self, mock_run_command):
        """Test that the 't' key triggers the run_tests action."""
        app = AgentTUI(project_dir=self.project_dir)
        async with app.run_test() as pilot:
            await pilot.press("t")
            mock_run_command.assert_called_once()

    @patch('shared.tui.Dashboard.run_command')
    async def test_run_linter_action(self, mock_run_command):
        """Test that the 'l' key triggers the run_linter action."""
        app = AgentTUI(project_dir=self.project_dir)
        async with app.run_test() as pilot:
            await pilot.press("l")
            mock_run_command.assert_called_once()

    @patch('shared.tui.Dashboard.run_command')
    async def test_run_formatter_action(self, mock_run_command):
        """Test that the 'f' key triggers the run_formatter action."""
        app = AgentTUI(project_dir=self.project_dir)
        async with app.run_test() as pilot:
            await pilot.press("f")
            mock_run_command.assert_called_once()

    @patch('shared.tui.get_project_summary')
    async def test_project_info_widget(self, mock_get_summary):
        """Test that the ProjectInfo widget updates correctly."""
        mock_get_summary.return_value = "Test Project Summary"

        app = AgentTUI(project_dir=self.project_dir)
        async with app.run_test() as pilot:
            await pilot.pause()
            project_info = pilot.app.screen.query_one(ProjectInfo)
            project_info.update_info()
            await pilot.pause()
            self.assertEqual(str(project_info.renderable).strip(), "Test Project Summary")

    @patch('shared.tui.get_latest_log_file')
    async def test_log_viewer_widget(self, mock_get_log_file):
        """Test that the log viewer widget updates correctly."""
        log_file = self.project_dir / "test.log"
        log_file.write_text("Log line 1\nLog line 2")
        mock_get_log_file.return_value = log_file

        app = AgentTUI(project_dir=self.project_dir)
        async with app.run_test() as pilot:
            await pilot.pause()
            dashboard = pilot.app.screen
            dashboard.update_log_viewer()
            await pilot.pause()
            log_viewer = dashboard.query_one("#log-viewer")

            # To reliably get the content, we can check the lines in the RichLog
            log_content = "".join(line.text for line in log_viewer.lines)
            self.assertIn("Log line 1", log_content)
            self.assertIn("Log line 2", log_content)

        log_file.unlink()

if __name__ == "__main__":
    unittest.main()
