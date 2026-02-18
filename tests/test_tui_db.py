import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import shutil
import tempfile

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))

from textual.widgets import Label, Button, RichLog, DataTable, Input, Select, TabbedContent, TextArea
from textual.containers import Container
from shared.tui import AgentTUI, DatabaseTab

class MockServicesTab(Container):
    """Mock ServicesTab to avoid background timers in tests."""
    def __init__(self, project_dir, **kwargs):
        # We absorb the project_dir argument and don't pass it to Container
        super().__init__(**kwargs)

class TestTUIDatabase(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Patch ServicesTab to avoid side effects
        self.patcher_services = patch("shared.tui.ServicesTab", MockServicesTab)
        self.patcher_services.start()

        self.test_dir = Path(tempfile.mkdtemp())
        self.project_dir = self.test_dir / "project"
        self.project_dir.mkdir()

        # Mock init_db to prevent side effects
        self.patcher_db = patch("shared.tui.init_db")
        self.mock_init_db = self.patcher_db.start()

    def tearDown(self):
        self.patcher_services.stop()
        self.patcher_db.stop()
        shutil.rmtree(self.test_dir)

    async def test_database_tab_structure(self):
        """Test that the database tab has the expected widgets."""
        app = AgentTUI(project_dir=self.project_dir)
        async with app.run_test(size=(120, 40)) as pilot:
            # Switch to database tab
            tabbed_content = app.query_one("#main-tabs")
            tabbed_content.active = "tab-database"
            await pilot.pause()

            # Check if DatabaseTab exists
            db_tab = app.query_one(DatabaseTab)
            self.assertIsNotNone(db_tab)

            # Check for buttons
            self.assertTrue(db_tab.query_one("#btn-db-connect", Button))
            self.assertTrue(db_tab.query_one("#btn-db-run", Button))

            # Check for inputs
            self.assertTrue(db_tab.query_one("#input-db-query", TextArea))
            self.assertTrue(db_tab.query_one("#sel-query-mode", Select))

            # Check for log and table
            self.assertTrue(db_tab.query_one("#db-log", RichLog))
            self.assertTrue(db_tab.query_one("#db-results-table", DataTable))

    @patch("shared.tui_database.detect_connection_string")
    async def test_detect_db(self, mock_detect):
        """Test DB detection logic."""
        mock_detect.return_value = "sqlite:///test.db"

        app = AgentTUI(project_dir=self.project_dir)
        async with app.run_test(size=(120, 40)) as pilot:
            # Switch to database tab
            tabbed_content = app.query_one("#main-tabs")
            tabbed_content.active = "tab-database"
            await pilot.pause()

            db_tab = app.query_one(DatabaseTab)

            # Click detect button
            await pilot.click("#btn-db-connect")
            await pilot.pause() # Wait for event handling

            # Check updates
            lbl = db_tab.query_one("#lbl-db-conn", Label)
            self.assertIn("Connected", str(lbl.renderable))

    @patch("shared.tui_database.SqlLabManager")
    @patch("shared.tui_database.detect_connection_string")
    async def test_execute_sql(self, mock_detect, MockSqlLabManager):
        """Test SQL execution."""
        mock_detect.return_value = "sqlite:///test.db"

        # Setup mock manager instance
        mock_manager = MockSqlLabManager.return_value
        mock_manager.execute_query.return_value = {"success": True, "columns": ["id"], "rows": [{"id": 1}]}
        # Mock list_tables to avoid issues during connection
        mock_manager.list_tables.return_value = []

        app = AgentTUI(project_dir=self.project_dir)
        async with app.run_test(size=(120, 40)) as pilot:
            # Switch to database tab
            tabbed_content = app.query_one("#main-tabs")
            tabbed_content.active = "tab-database"
            await pilot.pause()

            db_tab = app.query_one(DatabaseTab)

            # Detect DB first
            await pilot.click("#btn-db-connect")
            await pilot.pause()

            # Ensure SQL mode
            mode_select = db_tab.query_one("#sel-query-mode", Select)
            mode_select.value = "SQL"

            # Enter query
            inp = db_tab.query_one("#input-db-query", TextArea)
            inp.text = "SELECT 1"

            # Execute
            await pilot.click("#btn-db-run")
            await pilot.pause() # Wait for execution

            # Check call
            mock_manager.execute_query.assert_called_with("SELECT 1")

            # Check log
            log = db_tab.query_one("#db-log", RichLog)
            # RichLog lines are list of Segments or similar, convert to str
            # Actually RichLog.lines is not directly accessible like that in all versions?
            # It's better to check if 'Success' text was written.
            # But RichLog stores lines internally.
            # We can check if `write` was called on it if we mock it, OR just assume it works if no error.
            # However, we are running full integration test.
            # We can check if the DataTable has columns.
            table = db_tab.query_one("#db-results-table", DataTable)
            self.assertEqual(len(table.columns), 1)

    @patch("shared.tui_database.generate_sql")
    @patch("shared.tui_database.detect_connection_string")
    async def test_generate_sql_safety(self, mock_detect, mock_generate):
        """Test that generating SQL populates input but does not execute."""
        mock_detect.return_value = "sqlite:///test.db"
        mock_generate.return_value = "SELECT * FROM safety"

        app = AgentTUI(project_dir=self.project_dir)
        async with app.run_test(size=(120, 40)) as pilot:
            tabbed_content = app.query_one("#main-tabs")
            tabbed_content.active = "tab-database"
            await pilot.pause()

            db_tab = app.query_one(DatabaseTab)
            await pilot.click("#btn-db-connect")
            await pilot.pause()

            # Switch to AI
            mode_select = db_tab.query_one("#sel-query-mode", Select)
            mode_select.value = "AI"

            # Enter query
            inp = db_tab.query_one("#input-db-query", TextArea)
            inp.text = "Show me safety"

            # Execute (Generate)
            await pilot.click("#btn-db-run")
            await pilot.pause()

            # Verify input updated
            self.assertEqual(inp.text, "SELECT * FROM safety")
            # Verify mode switched back to SQL
            self.assertEqual(mode_select.value, "SQL")

if __name__ == "__main__":
    unittest.main()
