import unittest
from shared.yaml_lab import YamlLabManager
import yaml
import json

class TestYamlLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = YamlLabManager()
        self.sample_data = {
            "store": {
                "book": [
                    {"category": "reference", "author": "Nigel Rees", "title": "Sayings of the Century", "price": 8.95},
                    {"category": "fiction", "author": "Evelyn Waugh", "title": "Sword of Honour", "price": 12.99}
                ],
                "bicycle": {
                    "color": "red",
                    "price": 19.95
                }
            }
        }

    def test_parse_path(self):
        self.assertEqual(self.manager._parse_path("a.b.c"), ["a", "b", "c"])
        self.assertEqual(self.manager._parse_path("a[0].b"), ["a", 0, "b"])
        self.assertEqual(self.manager._parse_path("a.0.b"), ["a", 0, "b"])
        self.assertEqual(self.manager._parse_path("key"), ["key"])

    def test_get(self):
        self.assertEqual(self.manager.get(self.sample_data, "store.bicycle.color"), "red")
        self.assertEqual(self.manager.get(self.sample_data, "store.book[0].author"), "Nigel Rees")
        self.assertEqual(self.manager.get(self.sample_data, "store.book[1].price"), 12.99)

        # Test nonexistent keys
        self.assertIsNone(self.manager.get(self.sample_data, "store.car"))
        self.assertIsNone(self.manager.get(self.sample_data, "store.book[5]"))

    def test_set(self):
        # Set existing
        self.manager.set(self.sample_data, "store.bicycle.color", "blue")
        self.assertEqual(self.sample_data["store"]["bicycle"]["color"], "blue")

        # Set new key
        self.manager.set(self.sample_data, "store.bicycle.brand", "Trek")
        self.assertEqual(self.sample_data["store"]["bicycle"]["brand"], "Trek")

        # Set list index
        self.manager.set(self.sample_data, "store.book[0].price", 10.00)
        self.assertEqual(self.sample_data["store"]["book"][0]["price"], 10.00)

        # Create nested structure
        data = {}
        self.manager.set(data, "a.b.c", 1)
        self.assertEqual(data, {"a": {"b": {"c": 1}}})

        # Create list in path
        data = {}
        self.manager.set(data, "a[0].b", 1)
        self.assertEqual(data, {"a": [{"b": 1}]})

    def test_delete(self):
        # Delete dict key
        self.manager.delete(self.sample_data, "store.bicycle.color")
        self.assertNotIn("color", self.sample_data["store"]["bicycle"])

        # Delete list item
        self.manager.delete(self.sample_data, "store.book[0]")
        self.assertEqual(len(self.sample_data["store"]["book"]), 1)
        self.assertEqual(self.sample_data["store"]["book"][0]["author"], "Evelyn Waugh")

    def test_merge(self):
        data1 = {"a": 1, "b": {"c": 2}}
        data2 = {"b": {"d": 3}, "e": 4}
        merged = self.manager.merge(data1, data2)

        self.assertEqual(merged["a"], 1)
        self.assertEqual(merged["b"]["c"], 2)
        self.assertEqual(merged["b"]["d"], 3)
        self.assertEqual(merged["e"], 4)

    def test_to_json(self):
        data = {"a": 1, "b": "test"}
        json_str = self.manager.to_json(data)
        parsed = json.loads(json_str)
        self.assertEqual(parsed, data)

    def test_validate(self):
        valid_yaml = """
        a: 1
        b:
          - 2
          - 3
        """
        self.assertTrue(self.manager.validate(valid_yaml))

        invalid_yaml = """
        a: 1
        b: [unclosed list
        """
        self.assertFalse(self.manager.validate(invalid_yaml))

    def test_load_yaml(self):
        # String loading
        data = self.manager.load_yaml("a: 1")
        self.assertEqual(data, {"a": 1})

        # Test error
        with self.assertRaises(ValueError):
            self.manager.load_yaml("[invalid")

if __name__ == '__main__':
    unittest.main()
