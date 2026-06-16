import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import ListView, ListItem, Button, RichLog, Label
from shared.tui_notebook import NotebookLabTab

class NotebookApp(App):
    def __init__(self, project_dir):
        super().__init__()
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        yield NotebookLabTab(self.project_dir)

class TestNotebookLabTab(unittest.IsolatedAsyncioTestCase):
    @patch("shared.tui_notebook.NotebookLabManager")
    async def test_mount_and_list(self, MockManager):
        # Setup mock manager
        manager = MockManager.return_value
        manager.list_notebooks.return_value = [Path("notebook1.ipynb"), Path("notebook2.ipynb")]

        app = NotebookApp(Path("."))
        async with app.run_test(size=(800, 600)) as pilot:
            tab = app.query_one(NotebookLabTab)
            list_view = tab.query_one("#notebook-list", ListView)

            # Check list content
            self.assertEqual(len(list_view.children), 2)
            # Textual list items are wrappers, we check labels
            labels = [str(item.query_one(Label).render()) for item in list_view.children]
            self.assertIn("notebook1.ipynb", labels)
            self.assertIn("notebook2.ipynb", labels)

            # Check initial buttons state (disabled)
            self.assertTrue(tab.query_one("#btn-notebook-inspect", Button).disabled)
            self.assertTrue(tab.query_one("#btn-notebook-clean", Button).disabled)

    @patch("shared.tui_notebook.NotebookLabManager")
    async def test_selection_and_actions(self, MockManager):
        manager = MockManager.return_value
        nb_path = Path("notebook1.ipynb")
        manager.list_notebooks.return_value = [nb_path]
        manager.inspect_notebook.return_value = {
            "kernel": "Python 3",
            "language": "python",
            "version": "3.8",
            "nbformat": "4.5",
            "cells": {"code": 1, "markdown": 1}
        }
        manager.clean_notebook = MagicMock(return_value=True)
        manager.convert_to_script = MagicMock(return_value=Path("notebook1.py"))
        manager.audit_notebook.return_value = []

        app = NotebookApp(Path("."))
        async with app.run_test(size=(800, 600)) as pilot:
            tab = app.query_one(NotebookLabTab)
            list_view = tab.query_one("#notebook-list", ListView)

            # Select the item
            # We need to find the index of the item to select it
            list_view.index = 0

            # Manually trigger the selection event logic because changing index programmatically
            # might not fire 'Selected' event in test environment as expected or requires waiting.
            # But let's try just setting index and waiting.
            await pilot.pause()

            # In Textual 0.64, ListView selection requires user interaction or explicit event posting.
            # Let's manually trigger on_notebook_selected logic for simplicity in test
            mock_event = MagicMock()
            mock_event.item = list_view.children[0]
            tab.on_notebook_selected(mock_event)

            # Check buttons enabled
            self.assertFalse(tab.query_one("#btn-notebook-inspect", Button).disabled)

            # Check Inspect output
            log = tab.query_one("#notebook-log", RichLog)
            # We can't easily read RichLog content in tests (it's internal), but we can verify manager call
            manager.inspect_notebook.assert_called_with(nb_path)

            # Test Clean
            pilot.app.query_one("#btn-notebook-clean").press()
            await pilot.pause()
            # clean_notebook runs in thread, wait a bit
            await pilot.pause()
            # Since we mocked it as a synchronous method but called it via asyncio.to_thread,
            # unittest.mock handles it (it's just a callable).
            # However, if clean_notebook is mocked as MagicMock, asyncio.to_thread calls it fine.
            # We verify it was called.
            # Note: asyncio.to_thread runs in a separate thread, so call args might be tricky to catch if we don't wait enough.
            # But let's check.
            # Actually, asyncio.to_thread awaits, so we are good.
            manager.clean_notebook.assert_called_with(nb_path)

            # Test Convert
            # Mock read_text for the path returned by convert_to_script
            # This is tricky because Path is instantiated inside the TUI logic or returned by manager.
            # The manager returns Path("notebook1.py").
            # The TUI calls out_path.read_text(). We need to patch Path.read_text or avoid it.
            # Easier: Mock the manager.convert_to_script to return a Mock object that acts like a Path
            mock_out_path = MagicMock(spec=Path)
            mock_out_path.name = "notebook1.py"
            mock_out_path.read_text.return_value = "print('hello')"
            manager.convert_to_script.return_value = mock_out_path

            pilot.app.query_one("#btn-notebook-convert").press()
            await pilot.pause()
            await pilot.pause()
            manager.convert_to_script.assert_called_with(nb_path)

            # Test Audit
            pilot.app.query_one("#btn-notebook-audit").press()
            await pilot.pause()
            manager.audit_notebook.assert_called_with(nb_path)

if __name__ == "__main__":
    unittest.main()
