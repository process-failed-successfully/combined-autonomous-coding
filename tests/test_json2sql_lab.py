import unittest
from shared.json2sql_lab import Json2SqlManager

class TestJson2SqlManager(unittest.TestCase):
    def setUp(self):
        self.manager = Json2SqlManager()

    def test_convert_single_object(self):
        json_str = '{"id": 1, "name": "Alice"}'
        result = self.manager.convert(json_str, "users")
        self.assertTrue(result["success"])
        self.assertEqual(result["sql"], "INSERT INTO users (id, name) VALUES (1, 'Alice');")

    def test_convert_list_of_objects(self):
        json_str = '[{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]'
        result = self.manager.convert(json_str, "users")
        self.assertTrue(result["success"])
        self.assertEqual(result["sql"], "INSERT INTO users (id, name) VALUES (1, 'Alice');\nINSERT INTO users (id, name) VALUES (2, 'Bob');")

    def test_convert_empty_list(self):
        json_str = '[]'
        result = self.manager.convert(json_str, "users")
        self.assertFalse(result["success"])
        self.assertIn("empty", result["error"])

    def test_convert_invalid_json(self):
        json_str = '{"id": 1, "name": "Alice"'
        result = self.manager.convert(json_str, "users")
        self.assertFalse(result["success"])
        self.assertIn("Invalid JSON", result["error"])

    def test_convert_missing_table_name(self):
        json_str = '[{"id": 1, "name": "Alice"}]'
        result = self.manager.convert(json_str, "")
        self.assertFalse(result["success"])
        self.assertIn("Table name is required", result["error"])

    def test_convert_string_escaping(self):
        json_str = '{"id": 1, "name": "O\'Connor"}'
        result = self.manager.convert(json_str, "users")
        self.assertTrue(result["success"])
        self.assertEqual(result["sql"], "INSERT INTO users (id, name) VALUES (1, 'O''Connor');")

    def test_convert_types(self):
        json_str = '{"id": 1, "is_active": true, "null_val": null, "score": 9.5}'
        result = self.manager.convert(json_str, "users")
        self.assertTrue(result["success"])
        self.assertEqual(result["sql"], "INSERT INTO users (id, is_active, null_val, score) VALUES (1, TRUE, NULL, 9.5);")

    def test_convert_nested_objects(self):
        json_str = '{"id": 1, "metadata": {"roles": ["admin", "user"]}}'
        result = self.manager.convert(json_str, "users")
        self.assertTrue(result["success"])
        # Should stringify the dict
        self.assertEqual(result["sql"], "INSERT INTO users (id, metadata) VALUES (1, '{\"roles\": [\"admin\", \"user\"]}');")


if __name__ == '__main__':
    unittest.main()
