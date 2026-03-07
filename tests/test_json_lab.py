import unittest
from unittest.mock import MagicMock
from shared.json_lab import JsonLabManager
import json

class TestJsonLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = JsonLabManager()
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

    def test_minify(self):
        data = {"a": 1, "b": 2}
        minified = self.manager.minify(data)
        self.assertEqual(minified, '{"a":1,"b":2}')

    def test_diff(self):
        d1 = {"a": 1, "b": 2}
        d2 = {"b": 2, "a": 1} # Same content, diff order

        # Should be empty diff because we sort keys
        diff = self.manager.diff(d1, d2)
        self.assertEqual(diff, "")

        d3 = {"a": 1, "b": 3}
        diff = self.manager.diff(d1, d3)
        # Check for presence of change without strict whitespace matching on the diff line prefix
        self.assertIn('"b": 2', diff)
        self.assertIn('"b": 3', diff)
        self.assertIn("-", diff)
        self.assertIn("+", diff)

    def test_validate(self):
        self.assertTrue(self.manager.validate('{"a": 1}'))
        self.assertTrue(self.manager.validate('[1, 2, 3]'))
        self.assertFalse(self.manager.validate('{a: 1}'))
        self.assertFalse(self.manager.validate('invalid'))

    def test_query(self):
        # Basic access
        self.assertEqual(self.manager.query(self.sample_data, "data['store']['bicycle']['color']"), "red")

        # Filtering
        result = self.manager.query(self.sample_data, "[b['title'] for b in data['store']['book'] if b['price'] < 10]")
        self.assertEqual(result, ["Sayings of the Century"])

        # Aggregation
        total_price = self.manager.query(self.sample_data, "sum(b['price'] for b in data['store']['book'])")
        self.assertAlmostEqual(total_price, 21.94)

        # Safety check (should fail if using banned builtins)
        with self.assertRaises(NameError):
            self.manager.query(self.sample_data, "__import__('os')")

if __name__ == '__main__':
    unittest.main()
