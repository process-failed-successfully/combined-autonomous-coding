import unittest
import sqlite3
import tempfile
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os

# Adjust path to include project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.db_query import _get_sqlite_schema, run_db_query_logic, _execute_sqlite
from shared.database_manager import DatabaseFramework

class TestDBQuery(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temp_dir.name)
        self.db_path = self.project_dir / "test.sqlite"

        # Create a dummy DB
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT);")
        cursor.execute("INSERT INTO users (name, email) VALUES ('Alice', 'alice@example.com');")
        cursor.execute("INSERT INTO users (name, email) VALUES ('Bob', 'bob@example.com');")
        conn.commit()
        conn.close()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_get_sqlite_schema(self):
        schema = _get_sqlite_schema(self.db_path)
        self.assertIn("CREATE TABLE users", schema)
        self.assertIn("id INTEGER PRIMARY KEY", schema)
        self.assertIn("name TEXT", schema)

    def test_execute_sqlite(self):
        # We capture stdout to verify output
        from io import StringIO
        captured_output = StringIO()
        original_stdout = sys.stdout
        sys.stdout = captured_output

        try:
            _execute_sqlite(self.db_path, "SELECT * FROM users ORDER BY name")
        finally:
            sys.stdout = original_stdout

        output = captured_output.getvalue()
        self.assertIn("Alice", output)
        self.assertIn("Bob", output)
        self.assertIn("alice@example.com", output)
        self.assertIn("(2 rows)", output)

    @patch("shared.db_query.DatabaseManager")
    @patch("shared.db_query.GeminiAgent")
    async def test_run_db_query_logic(self, MockAgent, MockDBManager):
        # Setup Mocks
        mock_db_manager = MockDBManager.return_value
        mock_db_manager.detect_framework.return_value = DatabaseFramework.UNKNOWN # We use sqlite file detection

        mock_agent_instance = MockAgent.return_value
        mock_agent_instance.run_agent_session = AsyncMock(return_value=(True, "SELECT * FROM users WHERE name = 'Alice'", []))

        # Run
        result = await run_db_query_logic(
            query="Find user Alice",
            project_dir=self.project_dir,
            agent_type="gemini",
            yes=True
        )

        self.assertTrue(result)

        # Verify Agent was called with prompt containing schema
        args, _ = mock_agent_instance.run_agent_session.call_args
        prompt = args[0]
        self.assertIn("CREATE TABLE users", prompt)
        self.assertIn("Find user Alice", prompt)

if __name__ == '__main__':
    unittest.main()
