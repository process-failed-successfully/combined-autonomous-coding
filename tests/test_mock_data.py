import unittest
import json
from shared.mock_data import MockDataGenerator


class TestMockDataGenerator(unittest.TestCase):
    def test_generate_basic_types(self) -> None:
        schema = {
            "id": "int",
            "score": "float",
            "active": "boolean",
            "uid": "uuid",
            "name": "string"
        }
        gen = MockDataGenerator(schema)
        data = gen.generate(10)
        self.assertEqual(len(data), 10)

        row = data[0]
        self.assertIsInstance(row["id"], int)
        self.assertIsInstance(row["score"], float)
        self.assertIsInstance(row["active"], bool)
        self.assertIsInstance(row["uid"], str)
        self.assertIsInstance(row["name"], str)

    def test_generate_complex_types(self) -> None:
        schema = {
            "dob": "date",
            "ts": "datetime",
            "email": "email",
            "full_name": "name",
            "category": {"type": "choice", "choices": ["A", "B", "C"]}
        }
        gen = MockDataGenerator(schema)
        data = gen.generate(5)

        row = data[0]
        # Just check basic format or type presence
        self.assertTrue("-" in row["dob"])
        self.assertTrue("T" in row["ts"])
        self.assertTrue("@" in row["email"])
        self.assertTrue(" " in row["full_name"])
        self.assertIn(row["category"], ["A", "B", "C"])

    def test_export_json(self) -> None:
        schema = {"id": "int"}
        gen = MockDataGenerator(schema)
        data = [{"id": 1}]
        output = gen.export(data, format="json")
        self.assertEqual(json.loads(output), data)

    def test_export_csv(self) -> None:
        schema = {"id": "int", "name": "string"}
        gen = MockDataGenerator(schema)
        data = [{"id": 1, "name": "test"}]
        output = gen.export(data, format="csv")
        self.assertIn("id,name", output)
        self.assertIn("1,test", output)

    def test_export_sql(self) -> None:
        schema = {"id": "int", "name": "string"}
        gen = MockDataGenerator(schema)
        data = [{"id": 1, "name": "test"}]
        output = gen.export(data, format="sql", table_name="users")
        self.assertIn("INSERT INTO users (id, name) VALUES (1, 'test');", output)


if __name__ == '__main__':
    unittest.main()
