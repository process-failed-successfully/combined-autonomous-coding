import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys

# Ensure shared is in path
sys.path.append(str(Path(__file__).parent.parent))

from shared.tui import DashboardTab
from textual.widgets import Label, ListView
from textual.containers import Container

class TestDashboardTab(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")

    @patch("shared.tui.HealthCalculator")
    @patch("shared.tui.TaskManager")
    @patch("shared.tui.get_suggestions")
    @patch("shared.tui.get_git_info")
    @patch("shared.tui.get_workflow_stage")
    async def test_initialization(self, mock_stage, mock_git, mock_sugg, mock_tm, mock_hc):
        # Setup mocks
        mock_git.return_value = {"branch": "main", "status": "Clean"}
        mock_stage.return_value = "IN_PROGRESS"

        tab = DashboardTab(self.project_dir)
        self.assertIsInstance(tab, Container)

    @patch("shared.tui.HealthCalculator")
    @patch("shared.tui.TaskManager")
    @patch("shared.tui.get_suggestions")
    @patch("shared.tui.get_git_info")
    @patch("shared.tui.get_workflow_stage")
    async def test_update_health(self, mock_stage, mock_git, mock_sugg, mock_tm, mock_hc):
        # Setup HealthCalculator mock
        mock_instance = mock_hc.return_value
        mock_instance.calculate.return_value = None
        mock_instance.grade = "A"
        mock_instance.score = 95

        tab = DashboardTab(self.project_dir)

        # Mock query_one to return a mock Label
        mock_label = MagicMock(spec=Label)
        tab.query_one = MagicMock(return_value=mock_label)

        # Call the async update method directly
        await tab._async_update_health()

        # Verify it updated the label
        tab.query_one.assert_called_with("#dash-health-lbl", Label)
        mock_label.update.assert_called()
        args = mock_label.update.call_args[0][0]
        self.assertIn("Grade:", args)
        self.assertIn("A", args)

    @patch("shared.tui.TaskManager")
    async def test_update_tasks(self, mock_tm):
        # Setup TaskManager mock
        mock_instance = mock_tm.return_value
        mock_task = MagicMock()
        mock_task.status = "Todo"
        mock_instance.fetch_all_tasks.return_value = [mock_task, mock_task] # 2 todos

        tab = DashboardTab(self.project_dir)
        mock_label = MagicMock(spec=Label)
        tab.query_one = MagicMock(return_value=mock_label)

        await tab._async_update_tasks()

        tab.query_one.assert_called_with("#dash-tasks-lbl", Label)
        mock_label.update.assert_called()
        self.assertIn("Todo: 2", mock_label.update.call_args[0][0])

    @patch("shared.tui.get_suggestions")
    async def test_update_suggestions(self, mock_sugg):
        mock_sugg.return_value = [{"reason": "Fix bug", "command": "fix"}]

        tab = DashboardTab(self.project_dir)
        mock_list = MagicMock(spec=ListView)
        tab.query_one = MagicMock(return_value=mock_list)

        tab.update_suggestions()

        tab.query_one.assert_called_with("#dash-suggest-list", ListView)
        mock_list.clear.assert_called()
        mock_list.append.assert_called()

if __name__ == "__main__":
    unittest.main()
