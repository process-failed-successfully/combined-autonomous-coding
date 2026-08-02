import unittest
from unittest.mock import MagicMock, patch
from shared.mysql_lab import MysqlLabManager, run_mysql_lab_logic
import argparse


class TestMysqlLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = MysqlLabManager(uri="mysql://user:pass@localhost:3306/db")

    def test_parse_uri(self):
        # Full URI
        kwargs = self.manager._parse_uri("mysql://user:pass@host:1234/mydb")
        self.assertEqual(kwargs['user'], 'user')
        self.assertEqual(kwargs['password'], 'pass')
        self.assertEqual(kwargs['host'], 'host')
        self.assertEqual(kwargs['port'], 1234)
        self.assertEqual(kwargs['database'], 'mydb')

        # Minimal URI
        kwargs = self.manager._parse_uri("mysql://localhost")
        self.assertEqual(kwargs['host'], 'localhost')
        self.assertEqual(kwargs['port'], 3306)

    @patch("shared.mysql_lab.pymysql")
    def test_connect(self, mock_pymysql):
        mock_conn = MagicMock()
        mock_pymysql.connect.return_value = mock_conn

        conn = self.manager.connect()

        self.assertEqual(conn, mock_conn)
        mock_pymysql.connect.assert_called_once()

        # Test caching
        conn2 = self.manager.connect()
        self.assertEqual(conn2, mock_conn)
        self.assertEqual(mock_pymysql.connect.call_count, 1)

    @patch("shared.mysql_lab.pymysql")
    def test_close(self, mock_pymysql):
        mock_conn = MagicMock()
        mock_pymysql.connect.return_value = mock_conn

        self.manager.connect()
        self.assertIsNotNone(self.manager._conn)

        self.manager.close()
        self.assertIsNone(self.manager._conn)
        mock_conn.close.assert_called_once()

    @patch.object(MysqlLabManager, "connect")
    def test_execute_query(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Mock SELECT result
        mock_cursor.description = [("id",), ("name",)]
        mock_cursor.fetchall.return_value = [{"id": 1, "name": "test"}]

        columns, rows = self.manager.execute_query("SELECT * FROM users")

        self.assertEqual(columns, ["id", "name"])
        self.assertEqual(rows, [{"id": 1, "name": "test"}])
        mock_cursor.execute.assert_called_once_with("SELECT * FROM users")

    @patch.object(MysqlLabManager, "execute_query")
    def test_get_tables(self, mock_execute_query):
        mock_execute_query.return_value = (["Tables_in_db"], [{"Tables_in_db": "users"}, {"Tables_in_db": "posts"}])

        tables = self.manager.get_tables()
        self.assertEqual(tables, ["users", "posts"])

    @patch.object(MysqlLabManager, "get_tables")
    @patch.object(MysqlLabManager, "execute_query")
    def test_get_schema(self, mock_execute_query, mock_get_tables):
        mock_get_tables.return_value = ["users"]
        mock_execute_query.return_value = (
            ["Table", "Create Table"],
            [{"Table": "users", "Create Table": "CREATE TABLE `users` (id int)"}]
        )

        schemas = self.manager.get_schema()
        self.assertEqual(schemas, ["CREATE TABLE `users` (id int);"])

    def test_export_csv(self):
        columns = ["id", "name"]
        rows = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]

        csv_str = self.manager.export_csv(columns, rows)
        self.assertIn("id,name", csv_str)
        self.assertIn("1,Alice", csv_str)
        self.assertIn("2,Bob", csv_str)

class TestMysqlLabCli(unittest.TestCase):
    @patch("shared.mysql_lab.pymysql")
    @patch.object(MysqlLabManager, "execute_query")
    def test_run_mysql_lab_logic_query(self, mock_execute_query, mock_pymysql):
        args = argparse.Namespace(
            command="mysql-lab",
            action="query",
            query="SELECT 1",
            uri="mysql://localhost",
            format="json"
        )

        mock_execute_query.return_value = (["1"], [{"1": 1}])

        with patch('sys.stdout', new=unittest.mock.MagicMock()) as mock_stdout:
            result = run_mysql_lab_logic(args)

        self.assertTrue(result)
        mock_execute_query.assert_called_once_with("SELECT 1")

if __name__ == '__main__':
    unittest.main()
