import unittest
from unittest.mock import MagicMock, patch

from shared.postgres_lab import PostgresLabManager

class TestPostgresLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = PostgresLabManager("postgresql://test:test@localhost:5432/test")

    @patch("shared.postgres_lab.psycopg2")
    def test_connect(self, mock_psycopg2):
        mock_conn = MagicMock()
        mock_psycopg2.connect.return_value = mock_conn

        conn = self.manager.connect()
        self.assertEqual(conn, mock_conn)
        mock_psycopg2.connect.assert_called_once_with("postgresql://test:test@localhost:5432/test")
        self.assertTrue(mock_conn.autocommit)

    def test_close(self):
        mock_conn = MagicMock()
        self.manager._conn = mock_conn
        self.manager.close()
        mock_conn.close.assert_called_once()
        self.assertIsNone(self.manager._conn)

    @patch("shared.postgres_lab.psycopg2")
    def test_execute_query(self, mock_psycopg2):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_psycopg2.connect.return_value = mock_conn

        # Setup context manager for cursor
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        # Setup query response
        mock_cursor.description = [("id",), ("name",)]
        mock_cursor.fetchall.return_value = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]

        columns, rows = self.manager.execute_query("SELECT id, name FROM users;")

        self.assertEqual(columns, ["id", "name"])
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["name"], "Alice")

        mock_cursor.execute.assert_called_once_with("SELECT id, name FROM users;")

    @patch("shared.postgres_lab.psycopg2")
    def test_execute_query_no_return(self, mock_psycopg2):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_psycopg2.connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        mock_cursor.description = None
        mock_cursor.rowcount = 1

        columns, rows = self.manager.execute_query("INSERT INTO users (name) VALUES ('Alice');")

        self.assertEqual(columns, ["Status", "Rows Affected"])
        self.assertEqual(rows[0]["Rows Affected"], 1)

    @patch.object(PostgresLabManager, "execute_query")
    def test_get_tables(self, mock_execute_query):
        mock_execute_query.return_value = (["tablename"], [{"tablename": "users"}, {"tablename": "posts"}])

        tables = self.manager.get_tables()
        self.assertEqual(tables, ["users", "posts"])

    @patch.object(PostgresLabManager, "execute_query")
    @patch.object(PostgresLabManager, "get_tables")
    def test_get_schema(self, mock_get_tables, mock_execute_query):
        mock_get_tables.return_value = ["users"]

        # Mock schema response
        mock_execute_query.return_value = (
            ["column_name", "data_type", "character_maximum_length", "is_nullable"],
            [
                {"column_name": "id", "data_type": "integer", "character_maximum_length": None, "is_nullable": "NO"},
                {"column_name": "name", "data_type": "character varying", "character_maximum_length": 255, "is_nullable": "YES"}
            ]
        )

        schemas = self.manager.get_schema()
        self.assertEqual(len(schemas), 1)

        schema_str = schemas[0]
        self.assertIn("CREATE TABLE users (", schema_str)
        self.assertIn("id integer NOT NULL", schema_str)
        self.assertIn("name character varying(255)", schema_str)

    def test_export_csv(self):
        columns = ["id", "name"]
        rows = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]

        csv_str = self.manager.export_csv(columns, rows)
        self.assertIn("id,name", csv_str)
        self.assertIn("1,Alice", csv_str)
        self.assertIn("2,Bob", csv_str)

if __name__ == "__main__":
    unittest.main()
