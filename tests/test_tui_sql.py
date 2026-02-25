import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import tempfile
import shutil

from textual.app import App, ComposeResult
from textual.widgets import Input, Button, TextArea, Select, Label
from shared.tui_sql import SqlLabTab

class SqlLabTestApp(App):
    def __init__(self, project_dir):
        super().__init__()
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        yield SqlLabTab(self.project_dir)

class TestSqlLabTab(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.project_dir = self.test_dir / "project"
        self.project_dir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    async def test_compose_structure(self):
        """Test that the SqlLabTab has the expected widgets."""
        app = SqlLabTestApp(self.project_dir)
        async with app.run_test() as pilot:
            # Check for AI Assistant widgets
            self.assertIsNotNone(app.query_one("#sql-ai-input", Input))
            self.assertIsNotNone(app.query_one("#sql-ai-agent", Select))
            self.assertIsNotNone(app.query_one("#btn-sql-ai-generate", Button))

            # Check for existing widgets
            self.assertIsNotNone(app.query_one("#sql-url-input", Input))
            self.assertIsNotNone(app.query_one("#sql-query-editor", TextArea))

    @patch("shared.tui_sql.SqlLabManager")
    @patch("shared.tui_sql.generate_sql", new_callable=AsyncMock)
    async def test_generate_ai_query(self, mock_generate_sql, MockSqlLabManager):
        """Test the AI query generation logic."""
        app = SqlLabTestApp(self.project_dir)

        # We need to inject mocks into the tab instance
        # Since run_test creates the app and mounts widgets, we need to access them via the app.

        # Mock Manager behavior
        mock_manager = MockSqlLabManager.return_value
        mock_manager.get_schema = MagicMock(return_value={"users": [{"name": "id", "type": "INTEGER"}]})
        mock_manager.engine = MagicMock() # For connection check

        # Mock generate_sql response
        mock_generate_sql.return_value = "SELECT * FROM users;"

        async with app.run_test() as pilot:
            tab = app.query_one(SqlLabTab)

            # Simulate Connection
            # We patch SqlLabManager but the tab instantiates it.
            # MockSqlLabManager is the class, so calling it returns mock_manager.

            # Manually set the manager to simulate connection (bypassing the connect button logic for this specific test aspect if needed,
            # but better to simulate the flow or just set it if we want to test generate specifically)
            tab.manager = mock_manager

            # Set input
            await pilot.click("#sql-ai-input")
            await pilot.press("S", "h", "o", "w", " ", "u", "s", "e", "r", "s")

            # Ensure input value is set (Textual inputs might need time or explicit setting in tests if typing is flaky)
            tab.query_one("#sql-ai-input", Input).value = "Show users"

            # Enable button (it's disabled by default, enabled on connect)
            # Since we manually set manager, we also need to enable the button manually or call connect_db
            tab.query_one("#btn-sql-ai-generate").disabled = False

            # Click Generate
            await pilot.click("#btn-sql-ai-generate")

            # Verify generate_sql called
            mock_generate_sql.assert_called_once()
            args = mock_generate_sql.call_args
            self.assertEqual(args[0][0], "Show users") # question
            self.assertIn("Table: users", args[0][1]) # schema string

            # Verify Editor content
            editor = tab.query_one("#sql-query-editor", TextArea)
            self.assertEqual(editor.text, "SELECT * FROM users;")

    @patch("shared.tui_sql.SqlLabManager")
    async def test_generate_ai_query_not_connected(self, MockSqlLabManager):
        """Test that it handles not connected state."""
        app = SqlLabTestApp(self.project_dir)
        async with app.run_test() as pilot:
            tab = app.query_one(SqlLabTab)
            # Ensure manager is None
            tab.manager = None

            # Button might be disabled, but we can try calling the handler directly
            # or force enable and click.
            tab.query_one("#btn-sql-ai-generate").disabled = False

            # Set input
            tab.query_one("#sql-ai-input", Input).value = "Show users"

            # Mock notify to verify warning
            tab.notify = MagicMock()

            await pilot.click("#btn-sql-ai-generate")

            tab.notify.assert_called_with("Not connected.", severity="warning")

if __name__ == "__main__":
    unittest.main()
