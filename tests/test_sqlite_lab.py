import unittest
from shared.sqlite_lab import SqliteLabManager

class TestSqliteLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = SqliteLabManager(":memory:")
        self.manager.connect()

    def tearDown(self):
        self.manager.close()

    def test_execute_query_create_table(self):
        query = "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);"
        columns, rows = self.manager.execute_query(query)
        self.assertEqual(columns, ["Status", "Rows Affected"])
        self.assertEqual(rows[0]["Status"], "Success")

    def test_execute_query_insert_select(self):
        self.manager.execute_query("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);")
        self.manager.execute_query("INSERT INTO users (name) VALUES ('Alice'), ('Bob');")

        columns, rows = self.manager.execute_query("SELECT * FROM users;")
        self.assertEqual(columns, ["id", "name"])
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["name"], "Alice")
        self.assertEqual(rows[1]["name"], "Bob")

    def test_get_tables(self):
        self.assertEqual(self.manager.get_tables(), [])
        self.manager.execute_query("CREATE TABLE users (id INTEGER PRIMARY KEY);")
        self.manager.execute_query("CREATE TABLE posts (id INTEGER PRIMARY KEY);")
        tables = self.manager.get_tables()
        self.assertIn("users", tables)
        self.assertIn("posts", tables)
        self.assertEqual(len(tables), 2)

    def test_get_schema(self):
        create_sql = "CREATE TABLE test_table (col1 TEXT)"
        self.manager.execute_query(create_sql)
        schema = self.manager.get_schema("test_table")
        self.assertIn("CREATE TABLE test_table (col1 TEXT)", schema)

        all_schemas = self.manager.get_schema()
        self.assertIn("CREATE TABLE test_table (col1 TEXT)", all_schemas)

    def test_export_csv(self):
        self.manager.execute_query("CREATE TABLE data (val TEXT);")
        self.manager.execute_query("INSERT INTO data (val) VALUES ('A'), ('B');")
        columns, rows = self.manager.execute_query("SELECT * FROM data;")
        csv_str = self.manager.export_csv(columns, rows)
        self.assertIn("val", csv_str)
        self.assertIn("A", csv_str)
        self.assertIn("B", csv_str)

    def test_invalid_query(self):
        with self.assertRaises(ValueError) as context:
            self.manager.execute_query("SELECT * FROM non_existent_table;")
        self.assertIn("SQLite Error", str(context.exception))

if __name__ == "__main__":
    unittest.main()
