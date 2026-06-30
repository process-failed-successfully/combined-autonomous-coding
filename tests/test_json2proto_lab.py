import unittest
from shared.json2proto_lab import Json2ProtoManager

class TestJson2ProtoManager(unittest.TestCase):

    def setUp(self):
        self.manager = Json2ProtoManager()

    def test_simple_object(self):
        json_str = '{"name": "test", "id": 1, "isActive": true}'
        result = self.manager.convert(json_str, "User")

        self.assertIn("message User {", result)
        self.assertIn("string name = 1;", result)
        self.assertIn("int64 id = 2;", result)
        self.assertIn("bool is_active = 3;", result)

    def test_nested_object(self):
        json_str = '{"user": {"name": "test"}}'
        result = self.manager.convert(json_str, "Root")

        self.assertIn("message User {", result)
        self.assertIn("string name = 1;", result)
        self.assertIn("message Root {", result)
        self.assertIn("User user = 1;", result)

    def test_array_of_objects(self):
        json_str = '{"items": [{"id": 1}]}'
        result = self.manager.convert(json_str, "Root")

        self.assertIn("message Item {", result)
        self.assertIn("int64 id = 1;", result)
        self.assertIn("message Root {", result)
        self.assertIn("repeated Item items = 1;", result)

    def test_root_array(self):
        json_str = '[{"id": 1}]'
        result = self.manager.convert(json_str, "Item")
        self.assertIn("message Item {", result)
        self.assertIn("repeated Item items = 1;", result)

if __name__ == '__main__':
    unittest.main()
