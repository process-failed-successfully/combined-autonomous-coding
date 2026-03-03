import unittest
import os
import tempfile
import json
from shared.ini_lab import IniLabManager


class TestIniLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = IniLabManager()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_file = os.path.join(self.temp_dir.name, "test.ini")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_set_and_get(self):
        self.manager.set(self.temp_file, "Database", "host", "localhost")
        self.manager.set(self.temp_file, "Database", "port", "5432")

        self.assertEqual(self.manager.get(self.temp_file, "Database", "host"), "localhost")
        self.assertEqual(self.manager.get(self.temp_file, "Database", "port"), "5432")
        self.assertEqual(self.manager.get(self.temp_file, "Database", "non_existent"), "")
        self.assertEqual(self.manager.get(self.temp_file, "Missing", "key"), "")

    def test_delete_key(self):
        self.manager.set(self.temp_file, "Section", "key1", "val1")
        self.manager.set(self.temp_file, "Section", "key2", "val2")

        self.manager.delete(self.temp_file, "Section", "key1")
        self.assertEqual(self.manager.get(self.temp_file, "Section", "key1"), "")
        self.assertEqual(self.manager.get(self.temp_file, "Section", "key2"), "val2")

    def test_delete_section(self):
        self.manager.set(self.temp_file, "S1", "k", "v")
        self.manager.set(self.temp_file, "S2", "k", "v")

        self.manager.delete(self.temp_file, "S1")
        self.assertNotIn("S1", self.manager.sections(self.temp_file))
        self.assertIn("S2", self.manager.sections(self.temp_file))

    def test_sections_and_keys(self):
        self.manager.set(self.temp_file, "SecA", "k1", "v1")
        self.manager.set(self.temp_file, "SecB", "k2", "v2")

        secs = self.manager.sections(self.temp_file)
        self.assertListEqual(sorted(secs), ["SecA", "SecB"])

        keys = self.manager.keys(self.temp_file, "SecA")
        self.assertListEqual(keys, ["k1"])

    def test_to_from_json(self):
        self.manager.set(self.temp_file, "Server", "host", "127.0.0.1")
        self.manager.set(self.temp_file, "Server", "port", "8080")

        js_str = self.manager.to_json(self.temp_file)
        data = json.loads(js_str)
        self.assertIn("Server", data)
        self.assertEqual(data["Server"]["host"], "127.0.0.1")

        new_file = os.path.join(self.temp_dir.name, "new.ini")
        new_json = json.dumps({"App": {"debug": "true"}})
        self.manager.from_json(new_json, new_file)

        self.assertEqual(self.manager.get(new_file, "App", "debug"), "true")


if __name__ == "__main__":
    unittest.main()
