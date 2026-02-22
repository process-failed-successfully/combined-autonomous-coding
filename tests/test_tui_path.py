import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
import shutil
import tempfile
from textual.app import App, ComposeResult
from textual.widgets import Input, Button, DataTable, RichLog, Select, Static, TabbedContent

from shared.tui_path import PathLabTab

class PathLabApp(App):
    """Harness app for testing PathLabTab."""
    def __init__(self, project_dir: Path):
        super().__init__()
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        yield PathLabTab(self.project_dir)

class TestPathLabTab(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    async def test_tab_composition(self):
        """Test that the tab components are present."""
        app = PathLabApp(self.test_dir)
        async with app.run_test() as pilot:
            tab = app.query_one(PathLabTab)
            self.assertIsNotNone(tab)

            # Check for Inspector widgets
            self.assertTrue(tab.query_one("#path-inspect-input", Input))
            self.assertTrue(tab.query_one("#btn-path-inspect", Button))
            self.assertTrue(tab.query_one("#path-inspect-table", DataTable))

            # Check for Calculator widgets
            self.assertTrue(tab.query_one("#select-path-op", Select))
            self.assertTrue(tab.query_one("#btn-path-calc", Button))
            self.assertTrue(tab.query_one("#lbl-path-result", Static))

            # Check for Globber widgets
            self.assertTrue(tab.query_one("#input-glob-base", Input))
            self.assertTrue(tab.query_one("#input-glob-pattern", Input))
            self.assertTrue(tab.query_one("#btn-path-glob", Button))
            self.assertTrue(tab.query_one("#glob-results-log", RichLog))

    @patch("shared.path_lab.PathLabManager.inspect_path")
    async def test_inspect_action(self, mock_inspect):
        """Test the inspect button action."""
        mock_inspect.return_value = {
            "exists": True,
            "is_file": True,
            "parts": ("a", "b"),
            "name": "b",
            "size": 123
        }

        app = PathLabApp(self.test_dir)
        async with app.run_test() as pilot:
            # Set input value directly
            app.query_one("#path-inspect-input", Input).value = "some/path"

            # Press button programmatically
            app.query_one("#btn-path-inspect", Button).press()

            # Wait for event processing
            await pilot.pause()

            # Check if manager method was called
            mock_inspect.assert_called_with("some/path")

            # Check table update
            table = app.query_one("#path-inspect-table", DataTable)
            self.assertGreater(len(table.rows), 0)

    @patch("shared.path_lab.PathLabManager.calculate_relative")
    async def test_calc_action(self, mock_calc):
        """Test the calculation button action."""
        mock_calc.return_value = "rel/path"

        app = PathLabApp(self.test_dir)
        async with app.run_test() as pilot:
            # Set operation
            select = app.query_one("#select-path-op", Select)
            select.value = "Relative Path"

            # Set input values
            app.query_one("#input-calc-1", Input).value = "target"
            app.query_one("#input-calc-2", Input).value = "base"

            # Press Calculate
            app.query_one("#btn-path-calc", Button).press()

            await pilot.pause()

            mock_calc.assert_called_with("target", "base")

            result_lbl = app.query_one("#lbl-path-result", Static)
            # Use str(render())
            self.assertIn("rel/path", str(result_lbl.render()))

if __name__ == "__main__":
    unittest.main()
