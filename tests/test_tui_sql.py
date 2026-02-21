import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from shared.tui_sql import SqlLabTab
from textual.app import App, ComposeResult
from textual.widgets import Input, Button, ListView, TextArea, DataTable, Label

class SqlLabApp(App):
    def compose(self) -> ComposeResult:
        yield SqlLabTab(Path("."))

@pytest.mark.asyncio
async def test_sql_lab_mount():
    with patch("shared.tui_sql.detect_connection_string", return_value="sqlite:///test.db"):
        app = SqlLabApp()
        async with app.run_test() as pilot:
            tab = app.query_one(SqlLabTab)
            assert tab.query_one("#sql-url-input", Input).value == "sqlite:///test.db"
            # Initially connect button is enabled, others disabled
            assert tab.query_one("#btn-sql-connect", Button).disabled == False
            assert tab.query_one("#btn-sql-refresh-tables", Button).disabled == True
            assert tab.query_one("#btn-sql-execute", Button).disabled == True

@pytest.mark.asyncio
async def test_sql_lab_connect_success():
    with patch("shared.tui_sql.detect_connection_string", return_value="sqlite:///test.db"), \
         patch("shared.tui_sql.SqlLabManager") as MockManager:

        mock_instance = MockManager.return_value
        # Mock engine context manager for connection test
        mock_conn = MagicMock()
        mock_instance.engine.connect.return_value.__enter__.return_value = mock_conn

        mock_instance.list_tables = MagicMock(return_value=["users", "posts"])

        app = SqlLabApp()
        async with app.run_test() as pilot:
            tab = app.query_one(SqlLabTab)

            # Click connect
            await pilot.click("#btn-sql-connect")

            # Wait for async operations? run_test usually handles pending events,
            # but since we use asyncio.to_thread, we might need a small pause or loop drain.
            # However, pilot.click waits for events.

            # Verify connected state
            lbl = tab.query_one("#lbl-sql-status", Label)
            assert "Connected" in str(lbl.render())
            assert tab.query_one("#btn-sql-refresh-tables", Button).disabled == False

            # Verify tables loaded
            list_view = tab.query_one("#sql-table-list", ListView)
            # Need to wait for list to populate?
            # Pilot should have waited.
            assert len(list_view.children) == 2
            # Use render() instead of renderable
            assert str(list_view.children[0].query_one(Label).render()) == "users"

@pytest.mark.asyncio
async def test_sql_lab_execute_query():
    with patch("shared.tui_sql.detect_connection_string", return_value="sqlite:///test.db"), \
         patch("shared.tui_sql.SqlLabManager") as MockManager:

        mock_instance = MockManager.return_value
        mock_instance.engine.connect.return_value.__enter__.return_value = MagicMock()

        # Mock execute query
        mock_instance.execute_query = MagicMock(return_value={
            "success": True,
            "columns": ["id", "name"],
            "rows": [{"id": 1, "name": "Alice"}]
        })

        mock_instance.list_tables = MagicMock(return_value=[])

        app = SqlLabApp()
        async with app.run_test() as pilot:
            tab = app.query_one(SqlLabTab)
            await pilot.click("#btn-sql-connect")

            # Set query
            tab.query_one("#sql-query-editor", TextArea).text = "SELECT * FROM users"

            # Click execute
            await pilot.click("#btn-sql-execute")

            # Verify results
            table = tab.query_one("#sql-results-table", DataTable)
            assert table.row_count == 1

            info = tab.query_one("#sql-result-info", Label)
            assert "1 rows returned" in str(info.render())
