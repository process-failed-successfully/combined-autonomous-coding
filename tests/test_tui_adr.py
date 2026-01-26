import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import ListView, Markdown, Button
from shared.tui_adr import ADRTab

class ADRTestApp(App):
    def __init__(self, project_dir):
        super().__init__()
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        yield ADRTab(self.project_dir)

class TestADRTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.app = ADRTestApp(self.project_dir)

    @patch("shared.tui_adr.ADRManager")
    async def test_load_adrs(self, MockManager):
        mock_instance = MockManager.return_value
        mock_instance.list_adrs.return_value = [
            {"title": "Use Python", "status": "Accepted", "filename": "0001-use-python.md"},
            {"title": "Use Textual", "status": "Proposed", "filename": "0002-use-textual.md"}
        ]

        async with self.app.run_test() as pilot:
            tab = self.app.query_one(ADRTab)
            list_view = tab.query_one("#adr-list", ListView)

            # Verify list populated (on_mount calls load_adrs)
            # Wait for any potential async mount ops
            await pilot.pause()

            self.assertEqual(len(list_view.children), 2)

    @patch("shared.tui_adr.ADRManager")
    async def test_selection(self, MockManager):
        mock_instance = MockManager.return_value
        mock_instance.list_adrs.return_value = [
            {"title": "Use Python", "status": "Accepted", "filename": "0001-use-python.md"}
        ]

        # Mock the path object returned by manager.adr_dir / filename
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = "# Title\nContent"

        # Mock the directory so __truediv__ returns our mock_path
        mock_dir = MagicMock()
        mock_dir.__truediv__.return_value = mock_path
        mock_instance.adr_dir = mock_dir

        async with self.app.run_test() as pilot:
            tab = self.app.query_one(ADRTab)
            list_view = tab.query_one("#adr-list", ListView)

            await pilot.pause()

            # Select first item
            list_view.index = 0
            await pilot.press("enter")
            await pilot.pause()

            self.assertEqual(tab.selected_adr, "0001-use-python.md")

    @patch("shared.tui_adr.ADRManager")
    async def test_create_adr(self, MockManager):
        mock_instance = MockManager.return_value
        mock_instance.list_adrs.return_value = []

        async with self.app.run_test() as pilot:
            tab = self.app.query_one(ADRTab)

            # Open create pane
            await pilot.click("#btn-adr-create")

            # Fill form
            input_title = tab.query_one("#adr-new-title")
            input_title.value = "New Decision"

            # Click submit
            await pilot.click("#btn-adr-submit")
            await pilot.pause()

            # Verify manager call
            mock_instance.create_adr.assert_called()
            args = mock_instance.create_adr.call_args
            self.assertEqual(args[0][0], "New Decision")

if __name__ == "__main__":
    unittest.main()
