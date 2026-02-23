import unittest
from shared.sql_game import SqlGameEngine, SqlGameLevel, SqlGameGenerator

class TestSqlGameEngine(unittest.TestCase):
    def setUp(self):
        self.engine = SqlGameEngine()
        self.level = SqlGameLevel(
            name="Test Level",
            description="Select all from table",
            setup_sql="CREATE TABLE test (id INT, val TEXT); INSERT INTO test VALUES (1, 'a');",
            solution_sql="SELECT * FROM test;",
            hint="Use SELECT *"
        )

    def test_validate_correct(self):
        result = self.engine.validate("SELECT * FROM test;", self.level)
        self.assertTrue(result["success"])
        self.assertEqual(result["rows"], [(1, 'a')])

    def test_validate_incorrect_rows(self):
        result = self.engine.validate("SELECT * FROM test WHERE id = 2;", self.level)
        self.assertFalse(result["success"])
        self.assertIn("Row count mismatch", result["error"])

    def test_validate_incorrect_columns(self):
        result = self.engine.validate("SELECT id FROM test;", self.level)
        self.assertFalse(result["success"])
        self.assertIn("Column count mismatch", result["error"])

    def test_validate_syntax_error(self):
        result = self.engine.validate("SELECT * FROM;", self.level)
        self.assertFalse(result["success"])
        self.assertIn("SQL Error", result["error"])

class TestSqlGameGenerator(unittest.TestCase):
    def test_generate_levels(self):
        generator = SqlGameGenerator()
        levels = generator.generate_levels()
        self.assertTrue(len(levels) > 0)
        self.assertIsInstance(levels[0], SqlGameLevel)
        self.assertEqual(levels[0].name, "Level 1: The SELECT Statement")

if __name__ == "__main__":
    unittest.main()
