import unittest
from shared.jq_lab import JqLabManager


class TestJqLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = JqLabManager()
        self.data = {
            "store": {
                "book": [
                    {
                        "category": "reference",
                        "author": "Nigel Rees",
                        "title": "Sayings of the Century",
                        "price": 8.95
                    },
                    {
                        "category": "fiction",
                        "author": "Evelyn Waugh",
                        "title": "Sword of Honour",
                        "price": 12.99
                    }
                ],
                "bicycle": {
                    "color": "red",
                    "price": 19.95
                }
            }
        }

    def test_evaluate_basic(self):
        res = self.manager.evaluate(self.data, ".store.bicycle.color")
        self.assertEqual(res, "red")

    def test_evaluate_array_index(self):
        res = self.manager.evaluate(self.data, ".store.book[1].author")
        self.assertEqual(res, "Evelyn Waugh")

    def test_evaluate_array_iteration(self):
        res = self.manager.evaluate(self.data, ".store.book[].title")
        self.assertEqual(res, ["Sayings of the Century", "Sword of Honour"])

    def test_evaluate_filter(self):
        res = self.manager.evaluate(self.data, ".store.book[] | select(.price < 10) | .title")
        self.assertEqual(res, "Sayings of the Century")

    def test_evaluate_invalid_expr(self):
        with self.assertRaises(ValueError):
            self.manager.evaluate(self.data, ".store[")

    def test_evaluate_no_match(self):
        res = self.manager.evaluate(self.data, ".nonexistent")
        self.assertIsNone(res)

    def test_evaluate_empty_expr(self):
        res = self.manager.evaluate(self.data, "")
        self.assertEqual(res, self.data)
