import unittest
from unittest.mock import MagicMock, patch
from textual.widgets import Button, DataTable, Checkbox
from textual.app import App, ComposeResult
from pathlib import Path
from shared.tui_chaos import ChaosTab

class ChaosTestApp(App):
    def __init__(self, tab):
        super().__init__()
        self.tab = tab

    def compose(self) -> ComposeResult:
        yield self.tab

class TestChaosTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.mock_manager_instance = MagicMock()

        # Mock experiments
        mock_exp = MagicMock()
        mock_exp.description = "Test Description"
        # When accessing experiments dict
        self.mock_manager_instance.experiments = {"test-exp": MagicMock(return_value=mock_exp)}

        # Patch ChaosManager in shared.tui_chaos
        self.patcher = patch("shared.tui_chaos.ChaosManager")
        self.mock_manager_class = self.patcher.start()
        self.mock_manager_class.return_value = self.mock_manager_instance

    async def asyncTearDown(self):
        self.patcher.stop()

    async def test_mount_and_load(self):
        tab = ChaosTab(self.project_dir)
        app = ChaosTestApp(tab)
        async with app.run_test() as pilot:
            # Check table columns
            table = app.query_one("#chaos-table", DataTable)
            self.assertEqual(len(table.columns), 2) # Name, Description

            # Check loaded experiments
            self.assertEqual(table.row_count, 1)
            self.assertEqual(table.get_row("test-exp")[0], "test-exp")

    async def test_selection_enables_button(self):
        tab = ChaosTab(self.project_dir)
        app = ChaosTestApp(tab)
        async with app.run_test() as pilot:
            run_btn = app.query_one("#btn-chaos-run", Button)
            self.assertTrue(run_btn.disabled)

            table = app.query_one("#chaos-table", DataTable)
            table.move_cursor(row=0)
            await pilot.press("enter")

            self.assertFalse(run_btn.disabled)
            self.assertEqual(tab.selected_experiment, "test-exp")

    async def test_run_experiment(self):
        self.mock_manager_instance.run.return_value = True

        tab = ChaosTab(self.project_dir)
        app = ChaosTestApp(tab)
        async with app.run_test() as pilot:
            # Select experiment
            table = app.query_one("#chaos-table", DataTable)
            table.move_cursor(row=0)
            await pilot.press("enter")

            # Click run
            pilot.app.query_one("#btn-chaos-run").press()
            await pilot.pause()

            # Verify manager instantiated (happens inside run_experiment for the second time)
            # The first time is in __init__
            self.assertTrue(self.mock_manager_class.call_count >= 1)

            # Verify run called on the instance
            self.mock_manager_instance.run.assert_called()
            args, kwargs = self.mock_manager_instance.run.call_args
            self.assertEqual(args[0], "test-exp")
            self.assertTrue(kwargs['dry_run']) # Default is True
            self.assertTrue(kwargs['yes']) # Should be True for TUI

    async def test_run_experiment_live(self):
        self.mock_manager_instance.run.return_value = True

        tab = ChaosTab(self.project_dir)
        app = ChaosTestApp(tab)
        async with app.run_test() as pilot:
            # Select experiment
            table = app.query_one("#chaos-table", DataTable)
            table.move_cursor(row=0)
            await pilot.press("enter")

            # Uncheck dry run
            chk = app.query_one("#chk-chaos-dry", Checkbox)
            chk.value = False

            # Click run
            pilot.app.query_one("#btn-chaos-run").press()
            await pilot.pause()

            # Verify manager called with dry_run=False
            # Get last call
            args, kwargs = self.mock_manager_instance.run.call_args
            self.assertFalse(kwargs['dry_run'])
