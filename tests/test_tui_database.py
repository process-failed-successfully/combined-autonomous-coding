import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from shared.tui_database import DatabaseTab


class TestDatabaseTab(unittest.IsolatedAsyncioTestCase):
    @patch("shared.tui_database.detect_connection_string")
    @patch("shared.tui_database.SqlLabManager")
    async def test_connect_db(self, MockManager, mock_detect):
        # Setup
        mock_detect.return_value = "sqlite:///test.db"
        mock_manager_instance = MockManager.return_value
        mock_manager_instance.list_tables.return_value = ["table1", "table2"]
        mock_manager_instance.get_schema.return_value = {"table1": []}

        # Init Tab
        tab = DatabaseTab(Path("."))

        # Mock UI elements
        tab.query_one = MagicMock()  # type: ignore[method-assign]
        lbl_conn = MagicMock()
        list_view = MagicMock()
        tab.query_one.side_effect = lambda selector, type=None: {
            "#lbl-db-conn": lbl_conn,
            "#db-table-list": list_view,
            "#db-results-table": MagicMock(),
        }.get(selector, MagicMock())

        # Action
        tab.connect_db()

        # Verify
        mock_detect.assert_called_with(Path("."))
        MockManager.assert_called_with("sqlite:///test.db")
        mock_manager_instance.list_tables.assert_called()
        lbl_conn.update.assert_called()
        # Verify list view population logic
        self.assertEqual(list_view.clear.call_count, 1)
        self.assertEqual(list_view.append.call_count, 2)

    @patch("shared.tui_database.detect_connection_string")
    @patch("shared.tui_database.SqlLabManager")
    async def test_run_query(self, MockManager, mock_detect):
        # Setup
        mock_detect.return_value = "sqlite:///test.db"
        mock_manager_instance = MockManager.return_value
        mock_manager_instance.execute_query.return_value = {
            "success": True,
            "columns": ["id", "name"],
            "rows": [{"id": 1, "name": "Alice"}],
            "rowcount": 1
        }

        tab = DatabaseTab(Path("."))

        # Mock UI elements setup BEFORE connect_db
        query_input = MagicMock()
        query_input.text = "SELECT * FROM users"
        mode_select = MagicMock()
        mode_select.value = "SQL"
        log = MagicMock()
        table = MagicMock()
        lbl_conn = MagicMock()
        list_view = MagicMock()

        tab.query_one = MagicMock()  # type: ignore[method-assign]
        tab.query_one.side_effect = lambda selector, type=None: {
            "#input-db-query": query_input,
            "#sel-query-mode": mode_select,
            "#db-log": log,
            "#db-results-table": table,
            "#lbl-db-conn": lbl_conn,
            "#db-table-list": list_view,
        }.get(selector, MagicMock())

        # Connect
        tab.connect_db()

        # Action
        await tab.run_query()

        # Verify
        mock_manager_instance.execute_query.assert_called_with("SELECT * FROM users")
        table.clear.assert_called()
        table.add_columns.assert_called_with("id", "name")
        table.add_rows.assert_called_with([['1', 'Alice']])

    @patch("shared.tui_database.generate_sql")
    @patch("shared.tui_database.detect_connection_string")
    @patch("shared.tui_database.SqlLabManager")
    async def test_run_query_ai(self, MockManager, mock_detect, mock_generate_sql):
        # Setup
        mock_detect.return_value = "sqlite:///test.db"
        mock_generate_sql.return_value = "SELECT * FROM generated"

        mock_manager_instance = MockManager.return_value
        # Important: Mock execution result to avoid failure in the execution phase
        mock_manager_instance.execute_query.return_value = {
            "success": True,
            "rowcount": 0,
            "rows": [],
            "columns": []
        }

        tab = DatabaseTab(Path("."))

        # Mock UI elements setup BEFORE connect_db
        query_input = MagicMock()
        query_input.text = "Show me users"
        mode_select = MagicMock()
        mode_select.value = "AI"
        agent_select = MagicMock()
        agent_select.value = "gemini"
        log = MagicMock()
        lbl_conn = MagicMock()
        list_view = MagicMock()
        table = MagicMock()

        tab.query_one = MagicMock()  # type: ignore[method-assign]
        tab.query_one.side_effect = lambda selector, type=None: {
            "#input-db-query": query_input,
            "#sel-query-mode": mode_select,
            "#sel-db-agent": agent_select,
            "#db-log": log,
            "#lbl-db-conn": lbl_conn,
            "#db-table-list": list_view,
            "#db-results-table": table,
        }.get(selector, MagicMock())

        # Connect
        tab.connect_db()

        # Action
        await tab.run_query()

        # Verify
        mock_generate_sql.assert_called()
        # Verify call args
        args, kwargs = mock_generate_sql.call_args
        self.assertEqual(kwargs.get('agent_type'), 'gemini')

        self.assertEqual(query_input.text, "SELECT * FROM generated")
        self.assertEqual(mode_select.value, "SQL")

        # Expect execution
        mock_manager_instance.execute_query.assert_called_with("SELECT * FROM generated")


if __name__ == "__main__":
    unittest.main()
