import unittest
from unittest.mock import MagicMock, patch, PropertyMock
from pathlib import Path
from textual.widgets import Label
from shared.tui_productivity import ProductivityTab

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
