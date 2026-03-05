import unittest
import json
from shared.mock_data import MockDataGenerator


class TestMockDataGenerator(unittest.TestCase):
    def test_generate_basic_types(self):
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

    def test_generate_complex_types(self):
        schema = {
            "dob": "date",
            "ts": "datetime",
            "email": "email",
            "full_name": "name",
            "category": {"type": "choice", "choices": ["A", "B", "C"]},
            "cc": "credit_card"
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

        # Test credit card format and Luhn
        cc = row["cc"]
        self.assertEqual(len(cc), 16)
        self.assertTrue(cc.isdigit())
        self.assertTrue(cc.startswith("4"))

        # Verify Luhn
        total = 0
        for i, digit in enumerate(reversed(cc[:-1])):
            n = int(digit)
            if i % 2 == 0:
                n *= 2
                if n > 9:
                    n -= 9
            total += n
        check_digit = (10 - (total % 10)) % 10
        self.assertEqual(int(cc[-1]), check_digit)

    def test_export_json(self):
        schema = {"id": "int"}
        gen = MockDataGenerator(schema)
        data = [{"id": 1}]
        output = gen.export(data, format="json")
        self.assertEqual(json.loads(output), data)

    def test_export_csv(self):
        schema = {"id": "int", "name": "string"}
        gen = MockDataGenerator(schema)
        data = [{"id": 1, "name": "test"}]
        output = gen.export(data, format="csv")
        self.assertIn("id,name", output)
        self.assertIn("1,test", output)

    def test_export_sql(self):
        schema = {"id": "int", "name": "string"}
        gen = MockDataGenerator(schema)
        data = [{"id": 1, "name": "test"}]
        output = gen.export(data, format="sql", table_name="users")
        self.assertIn("INSERT INTO users (id, name) VALUES (1, 'test');", output)


if __name__ == '__main__':
    unittest.main()
