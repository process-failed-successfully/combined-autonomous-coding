import unittest
import asyncio
import sys
from unittest.mock import MagicMock, patch, AsyncMock, PropertyMock
from pathlib import Path

# Ensure shared modules can be imported
sys.path.append(str(Path(__file__).parent.parent))

from textual.widgets import Label, Input, TextArea, DataTable, ListView
from shared.tui_day_planner import DayPlannerTab
from shared.day_planner import TimeBlock, DayPlan

class TestDayPlannerTab(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_proj")
        self.tab = DayPlannerTab(self.project_dir)

        # Mock managers
        self.tab.manager = MagicMock()
        # Textual's .app is a read-only property, we can't set it directly.
        # But we can patch it if we use it in methods (like start_focus)

        # Mock UI query methods
        self.tab.query_one = MagicMock()
        self.tab.notify = MagicMock()

    def test_load_tasks(self):
        # Mock unscheduled tasks
        mock_task = MagicMock()
        mock_task.title = "Test Task"
        mock_task.priority = "High"
        self.tab.manager.get_unscheduled_tasks.return_value = [mock_task]

        mock_list_view = MagicMock()
        self.tab.query_one.return_value = mock_list_view

        self.tab.load_tasks()

        self.tab.manager.get_unscheduled_tasks.assert_called()
        mock_list_view.clear.assert_called()
        mock_list_view.append.assert_called()

    def test_load_timeline(self):
        # Mock plan
        mock_block = TimeBlock(id="b1", start_time="09:00", duration=60, title="Work")
        mock_plan = DayPlan(date_str="2023-01-01", blocks=[mock_block])
        self.tab.manager.get_plan.return_value = mock_plan

        mock_table = MagicMock()
        self.tab.query_one.return_value = mock_table

        self.tab.load_timeline()

        self.tab.manager.get_plan.assert_called()
        mock_table.clear.assert_called()
        # Verify row added
        mock_table.add_row.assert_called_with("09:00", "60m", "Work", key="b1")

    async def test_add_block_success(self):
        # Mock inputs
        inputs = {
            "#dp-time-input": MagicMock(value="10:00"),
            "#dp-duration-input": MagicMock(value="30"),
            "#dp-title-input": MagicMock(value="Meeting"),
            "#dp-task-list": MagicMock()
        }

        def query_side_effect(selector, *args):
            return inputs.get(selector, MagicMock())

        self.tab.query_one.side_effect = query_side_effect

        # Mock manager
        self.tab.manager.add_block.return_value = "new-block-id"
        self.tab.refresh_view = MagicMock()

        await self.tab.add_block(use_selected_task=False)

        self.tab.manager.add_block.assert_called()
        self.tab.refresh_view.assert_called()
        self.tab.notify.assert_called_with("Block added.")

    async def test_add_block_fail_validation(self):
        # Missing time
        inputs = {
            "#dp-time-input": MagicMock(value=""),
            "#dp-duration-input": MagicMock(value="30"),
            "#dp-title-input": MagicMock(value="Meeting"),
        }
        self.tab.query_one.side_effect = lambda s, *a: inputs.get(s, MagicMock())

        await self.tab.add_block(use_selected_task=False)

        self.tab.manager.add_block.assert_not_called()
        self.tab.notify.assert_called_with("Time and Duration required.", severity="error")

    def test_save_notes(self):
        mock_editor = MagicMock()
        mock_editor.text = "My notes"
        self.tab.query_one.return_value = mock_editor

        self.tab.save_notes()

        self.tab.manager.update_notes.assert_called()
        self.tab.notify.assert_called_with("Notes saved.")

    def test_auto_schedule(self):
        self.tab.manager.auto_schedule.return_value = 5
        self.tab.refresh_view = MagicMock()

        self.tab.auto_schedule()

        self.tab.manager.auto_schedule.assert_called()
        self.tab.notify.assert_called_with("Auto-scheduled 5 tasks.")
        self.tab.refresh_view.assert_called()

    @patch('shared.tui_day_planner.DayPlannerTab.app', new_callable=PropertyMock)
    def test_start_focus(self, mock_app_prop):
        # Setup selected block
        self.tab.selected_block = "b1"

        # Mock app
        mock_app = MagicMock()
        mock_app_prop.return_value = mock_app
        mock_tabs = MagicMock()
        mock_app.query_one.return_value = mock_tabs

        # Mock plan to return a block
        mock_block = TimeBlock(id="b1", start_time="09:00", duration=60, title="Work")
        mock_plan = DayPlan(date_str="2023-01-01", blocks=[mock_block])
        self.tab.manager.get_plan.return_value = mock_plan

        self.tab.start_focus()

        # Verify tab switch
        mock_app.query_one.assert_called_with("TabbedContent")
        self.assertEqual(mock_tabs.active, "tab-focus")
        self.tab.notify.assert_called_with("Starting focus session.", severity="information")

if __name__ == '__main__':
    unittest.main()
