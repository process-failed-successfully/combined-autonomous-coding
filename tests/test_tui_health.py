import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import DataTable, Label, Button, ListView
from shared.tui import HealthTab

class HealthTestApp(App):
    def __init__(self, project_dir):
        super().__init__()
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        yield HealthTab(self.project_dir)

class TestTuiHealth(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.app = HealthTestApp(self.project_dir)

    async def test_mount(self):
        """Test that the tab mounts with correct widgets."""
        async with self.app.run_test() as pilot:
            # Check if widgets are present
            self.assertIsNotNone(pilot.app.query_one("#health-grade-lbl", Label))
            self.assertIsNotNone(pilot.app.query_one("#health-score-lbl", Label))
            self.assertIsNotNone(pilot.app.query_one("#health-breakdown-table", DataTable))
            self.assertIsNotNone(pilot.app.query_one("#btn-run-health", Button))

    @patch("shared.tui.HealthCalculator")
    async def test_run_health_check(self, mock_calc_cls):
        """Test that running health check updates the UI."""
        # Setup mock
        mock_calc = mock_calc_cls.return_value
        mock_calc.score = 85.0
        mock_calc.grade = "B"
        mock_calc.metrics = {
            "test_score": 30,
            "lint_score": 15,
            "complexity_score": 20,
            "security_score": 10,
            "dependency_score": 10
        }
        mock_calc.issues = ["Lint error"]

        # Mock calculate to do nothing
        mock_calc.calculate = MagicMock()

        async with self.app.run_test() as pilot:
            # Click button
            await pilot.click("#btn-run-health")

            # Wait for background task to complete and UI to update
            await pilot.pause(0.2)

            # Check UI updates
            grade_lbl = pilot.app.query_one("#health-grade-lbl", Label)
            self.assertIn("B", str(grade_lbl.render()))

            score_lbl = pilot.app.query_one("#health-score-lbl", Label)
            self.assertIn("85", str(score_lbl.render()))

            table = pilot.app.query_one("#health-breakdown-table", DataTable)
            self.assertEqual(table.row_count, 5)

            issues = pilot.app.query_one("#health-issues-list", ListView)
            self.assertEqual(len(issues.children), 1)
