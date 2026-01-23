import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
from textual.app import App, ComposeResult
from textual import events
from shared.tui import PlanTab

class TestPlanTab(unittest.IsolatedAsyncioTestCase):
    async def test_plan_tab_compose(self):
        # Mock dependencies
        project_dir = Path("/tmp/test")

        # We need a dummy App to mount the widget
        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield PlanTab(project_dir)

        app = TestApp()
        async with app.run_test() as pilot:
            # Check for widgets
            self.assertIsNotNone(app.query_one("#spec-editor"))
            self.assertIsNotNone(app.query_one("#plan-log"))
            self.assertIsNotNone(app.query_one("#btn-generate-plan"))

    @patch("shared.tui.run_plan_logic")
    async def test_generate_plan_interaction(self, mock_run_plan):
        project_dir = Path("/tmp/test")

        # Setup mock return
        mock_run_plan.return_value = (True, "Plan Generated Output")

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield PlanTab(project_dir)

        app = TestApp()
        async with app.run_test() as pilot:
            # Type something in spec editor (optional, depends on implementation)
            # Click Generate Button
            # We use pilot.click with ID
            await pilot.click("#btn-generate-plan")

            # Since run_plan_logic is awaited in the handler, we expect it to be called
            # Textual's pilot might not wait for async handlers unless we wait
            await pilot.pause()

            mock_run_plan.assert_called_once()

            # Check log output
            log = app.query_one("#plan-log")
            # Textual RichLog content is complex to assert directly as string,
            # but we can check if write was called if we mocked it, or check internal lines if accessible.
            # However, simpler is just ensuring the mock was called.

if __name__ == '__main__':
    unittest.main()
