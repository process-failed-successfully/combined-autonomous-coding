import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import DataTable, Button, RichLog, Label
from shared.tui_impact import ImpactTab
import asyncio
import sys

class ImpactTestApp(App):
    def __init__(self, project_dir):
        super().__init__()
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        yield ImpactTab(self.project_dir)

class TestImpactTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.app = ImpactTestApp(self.project_dir)

    @patch("shared.tui_impact.ImpactAnalyzer")
    async def test_analysis_population(self, MockAnalyzer):
        # Setup Mock
        mock_instance = MockAnalyzer.return_value

        # Mock behavior
        # get_changed_files -> ["utils.py"]
        # find_impacted_files -> ({"main.py", "utils.py"}, {"test_main.py"})

        mock_instance.build_graph = MagicMock()
        mock_instance.get_changed_files.return_value = ["utils.py"]
        mock_instance.find_impacted_files.return_value = ({"main.py", "utils.py"}, {"test_main.py"})

        async with self.app.run_test() as pilot:
            tab = self.app.query_one(ImpactTab)

            # Verify initial state
            changed_table = tab.query_one("#impact-changed-table", DataTable)
            source_table = tab.query_one("#impact-source-table", DataTable)
            tests_table = tab.query_one("#impact-tests-table", DataTable)

            self.assertEqual(changed_table.row_count, 0)
            self.assertTrue(tab.query_one("#btn-impact-run-tests").disabled)

            # Click Analyze Button
            await pilot.click("#btn-impact-analyze")
            await pilot.pause() # Wait for thread

            # Verify tables populated
            self.assertEqual(changed_table.row_count, 1)
            # get_row_at returns list of Cell objects or values depending on version,
            # usually it returns values in newer textual.
            # But let's check str(row[0]) to be safe if it's a rich object
            self.assertEqual(str(changed_table.get_row_at(0)[0]), "utils.py")

            # Impacted source should filter out changed file ("main.py" only)
            self.assertEqual(source_table.row_count, 1)
            self.assertEqual(str(source_table.get_row_at(0)[0]), "main.py")

            self.assertEqual(tests_table.row_count, 1)
            self.assertEqual(str(tests_table.get_row_at(0)[0]), "test_main.py")

            # Run button enabled
            self.assertFalse(tab.query_one("#btn-impact-run-tests").disabled)

    @patch("shared.tui_impact.ImpactAnalyzer")
    @patch("asyncio.create_subprocess_exec")
    async def test_run_tests(self, mock_exec, MockAnalyzer):
        # Setup Mock
        mock_instance = MockAnalyzer.return_value
        mock_instance.get_changed_files.return_value = ["utils.py"]
        mock_instance.find_impacted_files.return_value = ({"main.py"}, {"test_main.py"})

        # Mock subprocess
        mock_process = AsyncMock()
        mock_process.stdout.readline = AsyncMock(side_effect=[b"Test passed\n", b""])
        mock_process.stderr.readline = AsyncMock(return_value=b"")
        mock_process.wait.return_value = None
        mock_process.returncode = 0
        mock_exec.return_value = mock_process

        async with self.app.run_test() as pilot:
            tab = self.app.query_one(ImpactTab)

            # Populate first
            await pilot.click("#btn-impact-analyze")
            await pilot.pause()

            # Click Run Tests
            await pilot.click("#btn-impact-run-tests")
            await pilot.pause()

            # Check mock call
            mock_exec.assert_called_once()
            args = mock_exec.call_args[0]
            # args[0] is executable, args[1] is -m, args[2] is pytest, args[3...] are files
            self.assertIn("-m", args)
            self.assertIn("pytest", args)
            self.assertIn("test_main.py", args)

            # Check log (via status label)
            status = tab.query_one("#impact-status-lbl", Label)
            self.assertIn("Tests Passed", str(status.renderable))

if __name__ == "__main__":
    unittest.main()
