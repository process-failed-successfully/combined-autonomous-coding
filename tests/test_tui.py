import asyncio
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from textual.pilot import Pilot

from shared.tui import AgentTUI, Dashboard


class TestAgentTUI(unittest.TestCase):
    @patch("shared.tui.get_latest_log_file")
    @patch("shared.tui._run_history_logic")
    @patch("shared.tui.get_suggestions")
    @patch("shared.tui._run_enhanced_status_logic")
    def test_dashboard_widgets_display_correct_info(
        self, mock_status, mock_suggestions, mock_history, mock_get_log
    ):
        """Test that the dashboard widgets are present and display the correct information."""
        # Arrange
        mock_status.return_value = "Mocked Status Information"
        mock_suggestions.return_value = [
            {"command": "mock command", "reason": "mock reason"}
        ]
        mock_history.return_value = "Mocked History"

        # Mock the log file logic
        mock_log_file = MagicMock(spec=Path)
        mock_log_file.exists.return_value = True
        mock_get_log.return_value = mock_log_file

        async def run_test():
            # Act
            app = AgentTUI(project_dir=Path("."))
            async with app.run_test() as pilot:
                await pilot.pause(0.2)

                # Assert
                self.assertIsInstance(pilot.app.screen, Dashboard)

                status_widget = pilot.app.screen.query_one("#project-status")
                self.assertIn("Mocked Status Information", str(status_widget.render()))

                suggestions_widget = pilot.app.screen.query_one("#suggestions")
                self.assertIn("mock command", str(suggestions_widget.render()))

                history_widget = pilot.app.screen.query_one("#history")
                self.assertIn("Mocked History", str(history_widget.render()))

                pilot.app.screen.query_one("#log-viewer")

        # Run the async test
        asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main()
