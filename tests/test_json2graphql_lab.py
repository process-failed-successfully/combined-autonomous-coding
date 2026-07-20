import unittest
from shared.json2graphql_lab import Json2GraphQLManager

class TestJson2GraphQLLab(unittest.TestCase):
    def test_flat_json(self):
        manager = Json2GraphQLManager()
        json_str = '{"name": "test", "age": 30, "is_active": true}'
        result = manager.generate(json_str, root_name="User")

        self.assertIn("type User {", result)
        self.assertIn("name: String", result)
        self.assertIn("age: Int", result)
        self.assertIn("is_active: Boolean", result)
        self.assertIn("}", result)

    def test_nested_objects(self):
        manager = Json2GraphQLManager()
        json_str = '{"user": {"name": "Alice"}, "status": "ok"}'
        result = manager.generate(json_str, root_name="Response")

        self.assertIn("type User {", result)
        self.assertIn("name: String", result)
        self.assertIn("type Response {", result)
        self.assertIn("user: User", result)
        self.assertIn("status: String", result)

        # Check order: nested class should appear before root class
        self.assertLess(result.index("type User {"), result.index("type Response {"))

    def test_lists(self):
        manager = Json2GraphQLManager()
        json_str = '{"tags": ["a", "b"], "scores": [1, 2]}'
        result = manager.generate(json_str)

        self.assertIn("tags: [String]", result)
        self.assertIn("scores: [Int]", result)

    def test_nested_lists(self):
        manager = Json2GraphQLManager()
        json_str = '{"items": [{"id": 1, "name": "item1"}, {"id": 2, "name": "item2"}]}'
        result = manager.generate(json_str, root_name="Cart")

        self.assertIn("type ItemItem {", result)
        self.assertIn("id: Int", result)
        self.assertIn("name: String", result)
        self.assertIn("type Cart {", result)
        self.assertIn("items: [ItemItem]", result)

    def test_invalid_json(self):
        manager = Json2GraphQLManager()
        with self.assertRaises(ValueError):
            manager.generate("{invalid json")

    def test_list_root(self):
        manager = Json2GraphQLManager()
        json_str = '[{"id": 1}, {"id": 2}]'
        result = manager.generate(json_str, root_name="Item")

        self.assertIn("type Item {", result)
        self.assertIn("id: Int", result)

    def test_empty_object(self):
        manager = Json2GraphQLManager()
        json_str = '{}'
        result = manager.generate(json_str, root_name="Empty")

        self.assertIn("type Empty {", result)
        self.assertIn("_empty: String", result)

    def test_sanitize_identifier(self):
        manager = Json2GraphQLManager()
        json_str = '{"1st_item": "value", "class": "keyword", "a-b": 1}'
        result = manager.generate(json_str)

        self.assertIn("_1st_item: String", result)
        self.assertIn("class: String", result)
        self.assertIn("a_b: Int", result)

if __name__ == '__main__':
    unittest.main()
