import unittest
from shared.json2zod_lab import Json2ZodManager

class TestJson2ZodManager(unittest.TestCase):
    def setUp(self):
        self.manager = Json2ZodManager()

    def test_primitive_string(self):
        json_str = '"hello"'
        res = self.manager.convert(json_str)
        self.assertIn("export const Schema = z.string();", res)

    def test_primitive_number(self):
        json_str = '42'
        res = self.manager.convert(json_str)
        self.assertIn("export const Schema = z.number();", res)

    def test_primitive_boolean(self):
        json_str = 'true'
        res = self.manager.convert(json_str)
        self.assertIn("export const Schema = z.boolean();", res)

    def test_primitive_null(self):
        json_str = 'null'
        res = self.manager.convert(json_str)
        self.assertIn("export const Schema = z.any();", res)

    def test_empty_array(self):
        json_str = '[]'
        res = self.manager.convert(json_str)
        self.assertIn("export const Schema = z.array(z.any());", res)

    def test_string_array(self):
        json_str = '["a", "b"]'
        res = self.manager.convert(json_str)
        self.assertIn("export const Schema = z.array(z.string());", res)

    def test_simple_object(self):
        json_str = '{"name": "Alice", "age": 30}'
        res = self.manager.convert(json_str)
        self.assertIn("export const Schema = z.object({", res)
        self.assertIn("  name: z.string(),", res)
        self.assertIn("  age: z.number(),", res)

    def test_nested_object(self):
        json_str = '{"user": {"id": 1}}'
        res = self.manager.convert(json_str)
        self.assertIn("  user: z.object({", res)
        self.assertIn("    id: z.number(),", res)

    def test_object_array(self):
        json_str = '[{"id": 1}]'
        res = self.manager.convert(json_str)
        self.assertIn("export const Schema = z.array(", res)
        self.assertIn("z.object({", res)
        self.assertIn("id: z.number(),", res)

    def test_invalid_identifier(self):
        json_str = '{"first-name": "Alice"}'
        res = self.manager.convert(json_str)
        self.assertIn('  "first-name": z.string(),', res)

    def test_invalid_json(self):
        with self.assertRaises(ValueError):
            self.manager.convert('invalid json')

if __name__ == "__main__":
    unittest.main()
