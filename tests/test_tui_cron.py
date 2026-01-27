import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path
from textual.app import App, ComposeResult
from shared.tui_cron import CronLabTab

# Helper app
class CronLabTestApp(App):
    def compose(self) -> ComposeResult:
        yield CronLabTab(Path("."))

@pytest.mark.asyncio
async def test_tui_cron_tab():
    app = CronLabTestApp()
    async with app.run_test() as pilot:
        # Check initial state
        # In Textual 0.64, query_one might raise error if multiple or none, which is good assertion
        assert "Cron Expression Lab" in str(app.screen.query_one(".welcome-text").render())

        # Test Analyze
        input_widget = app.screen.query_one("#cron-expression")
        input_widget.value = "*/15 * * * *"

        # Click analyze
        app.screen.query_one("#btn-cron-analyze").focus()
        await pilot.press("enter")

        # Check output
        log = app.screen.query_one("#cron-runs-log")
        assert log

        # Mock AI for explain
        with patch("shared.cron_lab.CronLabManager.explain_expression", new_callable=AsyncMock) as mock_explain:
            mock_explain.return_value = "Explanation"
            app.screen.query_one("#btn-cron-explain").focus()
            await pilot.press("enter")
            mock_explain.assert_called_with("*/15 * * * *", "gemini")

        # Mock AI for generate
        input_desc = app.screen.query_one("#cron-description")
        input_desc.text = "Hourly"
        with patch("shared.cron_lab.CronLabManager.generate_expression", new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = "0 * * * *"
            app.screen.query_one("#btn-cron-generate").focus()
            await pilot.press("enter")
            mock_generate.assert_called_with("Hourly", "gemini")
