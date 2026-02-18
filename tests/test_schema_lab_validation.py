import unittest
from shared.schema_lab import SchemaLabManager

class TestSchemaLabValidation(unittest.TestCase):
    def setUp(self):
        self.manager = SchemaLabManager()

    def test_validate_type_string(self):
        schema = {"type": "string"}
        valid, msg = self.manager.validate_instance("hello", schema)
        self.assertTrue(valid)

        valid, msg = self.manager.validate_instance(123, schema)
        self.assertFalse(valid)
        self.assertIn("Expected string", msg)

    def test_validate_type_integer(self):
        schema = {"type": "integer"}
        valid, msg = self.manager.validate_instance(123, schema)
        self.assertTrue(valid)

        valid, msg = self.manager.validate_instance("123", schema)
        self.assertFalse(valid)

        # Boolean is subclass of int in Python, but JSON schema treats them as distinct
        # My implementation handles this explicitly
        valid, msg = self.manager.validate_instance(True, schema)
        self.assertFalse(valid)

    def test_validate_object_required(self):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            "required": ["name"]
        }

        valid, msg = self.manager.validate_instance({"name": "Alice", "age": 30}, schema)
        self.assertTrue(valid)

        valid, msg = self.manager.validate_instance({"age": 30}, schema)
        self.assertFalse(valid)
        self.assertIn("Missing required property 'name'", msg)

    def test_validate_nested_object(self):
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"}
                    },
                    "required": ["id"]
                }
            }
        }

        valid, msg = self.manager.validate_instance({"user": {"id": 1}}, schema)
        self.assertTrue(valid)

        valid, msg = self.manager.validate_instance({"user": {}}, schema)
        self.assertFalse(valid)
        self.assertIn("Missing required property 'id'", msg)

    def test_validate_array(self):
        schema = {
            "type": "array",
            "items": {"type": "integer"}
        }

        valid, msg = self.manager.validate_instance([1, 2, 3], schema)
        self.assertTrue(valid)

        valid, msg = self.manager.validate_instance([1, "2", 3], schema)
        self.assertFalse(valid)
        self.assertIn("Expected integer", msg)

    def test_validate_enum(self):
        schema = {"enum": ["A", "B"]}

        valid, msg = self.manager.validate_instance("A", schema)
        self.assertTrue(valid)

        valid, msg = self.manager.validate_instance("C", schema)
        self.assertFalse(valid)
        self.assertIn("not in enum", msg)

if __name__ == '__main__':
    unittest.main()
