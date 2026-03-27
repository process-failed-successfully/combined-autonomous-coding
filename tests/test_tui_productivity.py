import unittest
from unittest.mock import MagicMock, patch, PropertyMock
from pathlib import Path
from typing import Any
from textual.app import App, ComposeResult
from textual.widgets import Input, Button

# Since we want to test TUI app locally, we import the ProductivityTab
from shared.tui_productivity import ProductivityTab


class DummyApp(App[Any]):
    def __init__(self, project_dir: Path):
        super().__init__()
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        yield ProductivityTab(project_dir=self.project_dir)


class TestTUIProductivity(unittest.IsolatedAsyncioTestCase):
    async def test_custom_timer_inputs(self):
        project_dir = Path("/tmp/test_proj")
        project_dir.mkdir(parents=True, exist_ok=True)
        app = DummyApp(project_dir=project_dir)

        async with app.run_test() as pilot:
            # Wait for mount
            await pilot.pause()

            # Verify inputs exist with default values
            focus_input = app.query_one("#input-prod-focus-min", Input)
            break_input = app.query_one("#input-prod-break-min", Input)

            self.assertEqual(focus_input.value, "25")
            self.assertEqual(break_input.value, "5")

            # Change focus time to 15
            focus_input.value = "15"

            # Press start focus
            focus_btn = app.query_one("#btn-prod-start-focus", Button)
            focus_btn.press()

            # Wait a tick for UI updates
            await pilot.pause()

            # Let's check internal state of the tab
            tab = app.query_one(ProductivityTab)
            self.assertTrue(tab.timer_active)
            self.assertEqual(tab.initial_duration, 15 * 60)
            self.assertEqual(tab.remaining_seconds, 15 * 60)

            # Stop the timer
            stop_btn = app.query_one("#btn-prod-stop", Button)
            stop_btn.press()
            await pilot.pause()

            self.assertFalse(tab.timer_active)

            # Change break time to 10
            break_input.value = "10"

            # Press start break
            break_btn = app.query_one("#btn-prod-start-break", Button)
            break_btn.press()
            await pilot.pause()

            self.assertTrue(tab.timer_active)
            self.assertEqual(tab.initial_duration, 10 * 60)
            self.assertEqual(tab.remaining_seconds, 10 * 60)

            # Cleanup
            stop_btn.press()
            await pilot.pause()


class TestProductivityTab(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_proj")
        self.tab = ProductivityTab(self.project_dir)

        # Mock internal managers
        self.tab.manager = MagicMock()
        self.tab.task_manager = MagicMock()

        # Mock textual methods
        self.tab.query_one = MagicMock()
        self.tab.notify = MagicMock()
        self.tab.set_interval = MagicMock()

    def test_start_focus(self):
        # Mock select value
        mock_select = MagicMock()
        mock_select.value = "task-1"
        self.tab.query_one.return_value = mock_select

        self.tab.start_timer(1500, "work")

        self.assertTrue(self.tab.timer_active)
        self.assertEqual(self.tab.remaining_seconds, 1500)
        self.tab.manager.start_session.assert_called_with("work", "task-1")
        self.tab.set_interval.assert_called()

    def test_stop_timer(self):
        mock_timer = MagicMock()
        self.tab.timer = mock_timer
        self.tab.timer_active = True

        self.tab.stop_timer()

        self.assertFalse(self.tab.timer_active)
        self.tab.manager.stop_session.assert_called()
        mock_timer.stop.assert_called()

    def test_tick(self):
        self.tab.timer_active = True
        self.tab.remaining_seconds = 10
        self.tab.initial_duration = 100

        # Mock label updates
        mock_label = MagicMock()
        self.tab.query_one.return_value = mock_label
        self.tab.manager.get_today_stats.return_value = {
            "work_time": 0, "break_time": 0, "sessions_count": 0, "distractions": 0
        }

        self.tab.tick()

        self.assertEqual(self.tab.remaining_seconds, 9)
        # Should update display (we called query_one multiple times)
        self.assertTrue(self.tab.query_one.called)

    @patch('shared.tui_productivity.ProductivityTab.app', new_callable=PropertyMock)
    def test_tick_finish(self, mock_app_prop):
        mock_app = MagicMock()
        mock_app_prop.return_value = mock_app

        self.tab.timer_active = True
        self.tab.remaining_seconds = 1
        self.tab.initial_duration = 100
        self.tab.timer = MagicMock()
        self.tab.manager.get_today_stats.return_value = {
            "work_time": 0, "break_time": 0, "sessions_count": 0, "distractions": 0
        }

        # Mock label updates
        mock_label = MagicMock()
        self.tab.query_one.return_value = mock_label

        self.tab.tick()

        self.assertEqual(self.tab.remaining_seconds, 0)
        self.assertFalse(self.tab.timer_active)
        self.tab.manager.stop_session.assert_called()
        mock_app.bell.assert_called()


if __name__ == '__main__':
    unittest.main()
