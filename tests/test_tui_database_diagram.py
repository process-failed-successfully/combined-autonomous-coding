import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
import asyncio

from textual.app import App, ComposeResult
from textual.widgets import Tree, RichLog, Button

# We need to import the class we are testing
from shared.tui_database_diagram import DatabaseDiagramTab

# A simple app wrapper for testing
class TestApp(App):
    def compose(self) -> ComposeResult:
        yield DatabaseDiagramTab(Path("."))

class TestDatabaseDiagramTab(unittest.IsolatedAsyncioTestCase):
    @patch("shared.tui_database_diagram.get_schema_info")
    async def test_load_schema_and_render(self, mock_get_schema):
        # Mock schema return
        schema_text = """
        CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);
        CREATE TABLE posts (id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id));
        """
        mock_get_schema.return_value = (schema_text, Path("test.db"))

        app = TestApp()
        async with app.run_test() as pilot:
            # Wait for background tasks
            await pilot.pause(2.0)

            # Check if tree is populated
            tree = app.query_one(Tree)

            # Textual Tree nodes are a bit complex to inspect directly for text content recursively easily in test without expansion
            # But we can check if root has children.
            self.assertEqual(len(tree.root.children), 2) # users and posts

            # Check internal schema_data
            tab = app.query_one(DatabaseDiagramTab)
            self.assertEqual(len(tab.schema_data['tables']), 2)
            self.assertEqual(tab.schema_data['tables'][0]['name'], 'users')

    @patch("shared.tui_database_diagram.get_schema_info")
    async def test_no_schema(self, mock_get_schema):
        mock_get_schema.return_value = ("", None)

        app = TestApp()
        async with app.run_test() as pilot:
            await pilot.pause(0.5)
            tab = app.query_one(DatabaseDiagramTab)
            self.assertEqual(tab.schema_data, {})

if __name__ == '__main__':
    unittest.main()
