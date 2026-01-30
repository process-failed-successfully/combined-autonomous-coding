import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import shutil
import tempfile

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))

from textual.widgets import Label, Button, RichLog, DataTable, Input, Select, TabbedContent
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
            self.assertTrue(db_tab.query_one("#btn-db-detect", Button))
            self.assertTrue(db_tab.query_one("#btn-db-execute", Button))

            # Check for inputs
            self.assertTrue(db_tab.query_one("#input-db-query", Input))
            self.assertTrue(db_tab.query_one("#select-query-mode", Select))

            # Check for log and table
            self.assertTrue(db_tab.query_one("#db-schema-view", RichLog))
            self.assertTrue(db_tab.query_one("#db-results-table", DataTable))

    @patch("shared.tui.get_schema_info")
    async def test_detect_db(self, mock_get_info):
        """Test DB detection logic."""
        mock_get_info.return_value = ("CREATE TABLE t1...", Path("test.db"))

        app = AgentTUI(project_dir=self.project_dir)
        async with app.run_test(size=(120, 40)) as pilot:
            # Switch to database tab
            tabbed_content = app.query_one("#main-tabs")
            tabbed_content.active = "tab-database"
            await pilot.pause()

            db_tab = app.query_one(DatabaseTab)

            # Click detect button
            await pilot.click("#btn-db-detect")
            await pilot.pause() # Wait for event handling

            # Check updates
            lbl = db_tab.query_one("#lbl-db-status", Label)
            self.assertIn("Connected", str(lbl.render()))

    @patch("shared.tui.execute_sqlite")
    @patch("shared.tui.get_schema_info")
    async def test_execute_sql(self, mock_get_info, mock_execute):
        """Test SQL execution."""
        mock_get_info.return_value = ("SCHEMA", Path("test.db"))
        mock_execute.return_value = (["id"], [(1,)], 1)

        app = AgentTUI(project_dir=self.project_dir)
        async with app.run_test(size=(120, 40)) as pilot:
            # Switch to database tab
            tabbed_content = app.query_one("#main-tabs")
            tabbed_content.active = "tab-database"
            await pilot.pause()

            db_tab = app.query_one(DatabaseTab)

            # Detect DB first
            await pilot.click("#btn-db-detect")
            await pilot.pause()

            # Ensure SQL mode
            mode_select = db_tab.query_one("#select-query-mode", Select)
            mode_select.value = "SQL"

            # Enter query
            inp = db_tab.query_one("#input-db-query", Input)
            inp.value = "SELECT 1"

            # Execute
            await pilot.click("#btn-db-execute")
            await pilot.pause() # Wait for execution

            mock_execute.assert_called_with(Path("test.db"), "SELECT 1")

            # Check status
            status = db_tab.query_one("#lbl-query-status", Label)
            self.assertIn("Returned 1 rows", str(status.render()))

    @patch("shared.tui.generate_sql")
    @patch("shared.tui.get_schema_info")
    async def test_generate_sql_safety(self, mock_get_info, mock_generate):
        """Test that generating SQL populates input but does not execute."""
        mock_get_info.return_value = ("SCHEMA", Path("test.db"))
        mock_generate.return_value = "SELECT * FROM safety"

        app = AgentTUI(project_dir=self.project_dir)
        async with app.run_test(size=(120, 40)) as pilot:
            tabbed_content = app.query_one("#main-tabs")
            tabbed_content.active = "tab-database"
            await pilot.pause()

            db_tab = app.query_one(DatabaseTab)
            await pilot.click("#btn-db-detect")
            await pilot.pause()

            # Switch to Natural Language
            mode_select = db_tab.query_one("#select-query-mode", Select)
            mode_select.value = "Natural Language"

            # Enter query
            inp = db_tab.query_one("#input-db-query", Input)
            inp.value = "Show me safety"

            # Execute (Generate)
            await pilot.click("#btn-db-execute")
            await pilot.pause()

            # Verify input updated
            self.assertEqual(inp.value, "SELECT * FROM safety")
            # Verify mode switched back to SQL
            self.assertEqual(mode_select.value, "SQL")
            # Verify status
            status = db_tab.query_one("#lbl-query-status", Label)
            self.assertIn("Ready to execute", str(status.render()))

if __name__ == "__main__":
    unittest.main()
