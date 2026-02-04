import unittest
import json
from pathlib import Path
from shared.schema_lab import SchemaLabManager

class TestSchemaLab(unittest.TestCase):
    def setUp(self):
        self.manager = SchemaLabManager()

    def test_infer_primitives(self):
        self.assertEqual(self.manager.infer_schema("foo"), {"type": "string"})
        self.assertEqual(self.manager.infer_schema(123), {"type": "integer"})
        self.assertEqual(self.manager.infer_schema(12.34), {"type": "number"})
        self.assertEqual(self.manager.infer_schema(True), {"type": "boolean"})
        self.assertEqual(self.manager.infer_schema(None), {"type": "null"})

    def test_infer_list_homogenous(self):
        data = ["a", "b", "c"]
        schema = self.manager.infer_schema(data)
        self.assertEqual(schema["type"], "array")
        self.assertEqual(schema["items"], {"type": "string"})

    def test_infer_list_mixed(self):
        data = ["a", 1]
        schema = self.manager.infer_schema(data)
        self.assertEqual(schema["type"], "array")
        self.assertIn("anyOf", schema["items"])
        types = [x["type"] for x in schema["items"]["anyOf"]]
        self.assertIn("string", types)
        self.assertIn("integer", types)

    def test_infer_object(self):
        data = {"name": "Alice", "age": 30}
        schema = self.manager.infer_schema(data)
        self.assertEqual(schema["type"], "object")
        self.assertEqual(schema["properties"]["name"]["type"], "string")
        self.assertEqual(schema["properties"]["age"]["type"], "integer")

    def test_infer_nested_object(self):
        data = {"user": {"id": 1, "meta": {"active": True}}}
        schema = self.manager.infer_schema(data)
        self.assertEqual(schema["type"], "object")
        self.assertEqual(schema["properties"]["user"]["type"], "object")
        self.assertEqual(schema["properties"]["user"]["properties"]["meta"]["properties"]["active"]["type"], "boolean")

    def test_to_typescript_simple(self):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            }
        }
        ts = self.manager.to_typescript(schema, "Person")
        self.assertIn("export interface Person", ts)
        self.assertIn("name: string;", ts)
        self.assertIn("age: number;", ts)

    def test_to_typescript_nested(self):
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"}
                    }
                }
            }
        }
        ts = self.manager.to_typescript(schema, "Response")
        self.assertIn("export interface Response", ts)
        self.assertIn("user: ResponseUser;", ts)
        self.assertIn("export interface ResponseUser", ts)
        self.assertIn("id: number;", ts)

    def test_to_pydantic_simple(self):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            }
        }
        py = self.manager.to_pydantic(schema, "Person")
        self.assertIn("class Person(BaseModel):", py)
        self.assertIn("name: Optional[str] = None", py)
        self.assertIn("age: Optional[int] = None", py)

    def test_to_pydantic_nested(self):
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"}
                    }
                }
            }
        }
        py = self.manager.to_pydantic(schema, "Response")
        self.assertIn("class ResponseUser(BaseModel):", py)
        self.assertIn("id: Optional[int] = None", py)
        self.assertIn("class Response(BaseModel):", py)
        self.assertIn("user: Optional[ResponseUser] = None", py)

if __name__ == '__main__':
    unittest.main()
