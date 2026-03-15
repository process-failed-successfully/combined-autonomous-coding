import unittest
import json
from shared.json2csv_lab import Json2CsvManager

class TestJson2CsvLab(unittest.TestCase):
    def setUp(self):
        self.manager = Json2CsvManager()

    def test_flatten_simple_dict(self):
        data = {"name": "Alice", "age": 30}
        flattened = self.manager._flatten_dict(data)
        self.assertEqual(flattened, {"name": "Alice", "age": 30})

    def test_flatten_nested_dict(self):
        data = {"user": {"name": "Alice", "address": {"city": "Wonderland"}}}
        flattened = self.manager._flatten_dict(data)
        self.assertEqual(flattened, {"user.name": "Alice", "user.address.city": "Wonderland"})

    def test_flatten_with_list(self):
        data = {"name": "Alice", "hobbies": ["reading", "chess"]}
        flattened = self.manager._flatten_dict(data)
        self.assertEqual(flattened, {"name": "Alice", "hobbies": '["reading", "chess"]'})

    def test_convert_single_object(self):
        data = {"name": "Alice", "age": 30}
        csv_output = self.manager.convert(data)
        lines = csv_output.strip().split("\r\n")
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], "age,name")
        self.assertEqual(lines[1], "30,Alice")

    def test_convert_array_of_objects(self):
        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25}
        ]
        csv_output = self.manager.convert(data)
        lines = csv_output.strip().split("\r\n")
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0], "age,name")
        self.assertEqual(lines[1], "30,Alice")
        self.assertEqual(lines[2], "25,Bob")

    def test_convert_array_of_objects_missing_keys(self):
        data = [
            {"name": "Alice"},
            {"age": 25}
        ]
        csv_output = self.manager.convert(data)
        lines = csv_output.strip().split("\r\n")
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0], "age,name")
        self.assertEqual(lines[1], ",Alice")
        self.assertEqual(lines[2], "25,")

    def test_convert_invalid_data(self):
        with self.assertRaises(ValueError):
            self.manager.convert("not json")

        with self.assertRaises(ValueError):
            self.manager.convert(123)

if __name__ == '__main__':
    unittest.main()
