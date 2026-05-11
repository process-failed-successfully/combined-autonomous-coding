import unittest
import json
from shared.ini2json_lab import Ini2JsonManager


class TestIni2JsonManager(unittest.TestCase):
    def setUp(self):
        self.manager = Ini2JsonManager()

    def test_convert_simple(self):
        ini_data = """
[Section1]
key1 = value1
key2 = true

[Section2]
num = 42
float_val = 3.14
"""
        json_output = self.manager.convert(ini_data)
        data = json.loads(json_output)

        self.assertIn("Section1", data)
        self.assertEqual(data["Section1"]["key1"], "value1")
        self.assertTrue(data["Section1"]["key2"])

        self.assertIn("Section2", data)
        self.assertEqual(data["Section2"]["num"], 42)
        self.assertEqual(data["Section2"]["float_val"], 3.14)

    def test_convert_with_defaults(self):
        ini_data = """
[DEFAULT]
global_key = global_val

[App]
app_key = app_val
"""
        json_output = self.manager.convert(ini_data)
        data = json.loads(json_output)

        self.assertIn("DEFAULT", data)
        self.assertEqual(data["DEFAULT"]["global_key"], "global_val")

        self.assertIn("App", data)
        self.assertEqual(data["App"]["app_key"], "app_val")

    def test_convert_empty(self):
        ini_data = ""
        json_output = self.manager.convert(ini_data)
        data = json.loads(json_output)
        self.assertEqual(data, {})

    def test_invalid_ini(self):
        ini_data = """
[Section
invalid format
"""
        with self.assertRaises(ValueError):
            self.manager.convert(ini_data)


if __name__ == "__main__":
    unittest.main()
