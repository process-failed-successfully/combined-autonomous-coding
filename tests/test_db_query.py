import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from shared.db_query import get_schema_info, generate_sql, execute_sqlite

class TestDbQuery(unittest.IsolatedAsyncioTestCase):
    @patch("shared.db_query.DatabaseManager")
    @patch("shared.db_query.sqlite3")
    def test_get_schema_info_sqlite(self, mock_sqlite, mock_db_manager):
        # Setup
        mock_manager_instance = mock_db_manager.return_value
        mock_manager_instance.detect_framework.return_value = "unknown"

        mock_conn = mock_sqlite.connect.return_value
        mock_cursor = mock_conn.cursor.return_value
        mock_cursor.fetchall.return_value = [("CREATE TABLE test (id int);",)]

        # Mock glob to return a db file
        with patch("pathlib.Path.glob", return_value=[Path("test.db")]):
            schema, db_path = get_schema_info(Path("."))

        self.assertEqual(schema, "CREATE TABLE test (id int);")
        self.assertEqual(db_path, Path("test.db"))

    @patch("shared.db_query.Config")
    @patch("shared.db_query.GeminiAgent")
    async def test_generate_sql(self, mock_agent_cls, mock_config):
        # Setup
        mock_agent = mock_agent_cls.return_value
        # Mock run_agent_session to return (status, response, actions)
        mock_agent.run_agent_session = AsyncMock(return_value=("DONE", "SELECT * FROM test", []))

        sql = await generate_sql("Get all tests", "SCHEMA", Path("."), agent_type="gemini")

        self.assertEqual(sql, "SELECT * FROM test")

    @patch("shared.db_query.sqlite3")
    def test_execute_sqlite(self, mock_sqlite):
        mock_conn = mock_sqlite.connect.return_value
        mock_cursor = mock_conn.cursor.return_value

        # Mock description for SELECT
        mock_cursor.description = [("id", "int")]
        mock_cursor.fetchall.return_value = [(1,)]
        mock_cursor.rowcount = -1

        columns, rows, rowcount = execute_sqlite(Path("test.db"), "SELECT 1")

        self.assertEqual(columns, ["id"])
        self.assertEqual(rows, [(1,)])

if __name__ == "__main__":
    unittest.main()
