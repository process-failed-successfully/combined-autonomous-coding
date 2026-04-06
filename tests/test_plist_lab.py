import unittest
from shared.plist_lab import PlistManager

class TestPlistManager(unittest.TestCase):
    def setUp(self):
        self.manager = PlistManager()

    def test_json_to_plist_and_back(self):
        json_data = '{"key": "value", "list": [1, 2, 3]}'
        plist_data = self.manager.json_to_plist(json_data)
        self.assertIn("<key>key</key>", plist_data)

        json_back = self.manager.plist_to_json(plist_data)
        self.assertIn('"key": "value"', json_back)

if __name__ == "__main__":
    unittest.main()
