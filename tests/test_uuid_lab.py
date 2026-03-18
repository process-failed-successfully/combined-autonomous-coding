import unittest
import uuid
from shared.uuid_lab import UuidLabManager

class TestUuidLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = UuidLabManager()

    def test_generate_v4(self):
        results = self.manager.generate(version=4, count=5)
        self.assertEqual(len(results), 5)
        for u in results:
            self.assertTrue(self.manager.validate(u))
            obj = uuid.UUID(u)
            self.assertEqual(obj.version, 4)

    def test_generate_v1(self):
        results = self.manager.generate(version=1, count=1)
        u = results[0]
        obj = uuid.UUID(u)
        self.assertEqual(obj.version, 1)

    def test_generate_v3(self):
        name = "test.com"
        ns = "DNS"
        results = self.manager.generate(version=3, count=1, namespace=ns, name=name)
        u = results[0]
        obj = uuid.UUID(u)
        self.assertEqual(obj.version, 3)
        # Check determinism
        u2 = uuid.uuid3(uuid.NAMESPACE_DNS, name)
        self.assertEqual(str(u2), u)

    def test_generate_v5(self):
        name = "test.com"
        ns = "DNS"
        results = self.manager.generate(version=5, count=1, namespace=ns, name=name)
        u = results[0]
        obj = uuid.UUID(u)
        self.assertEqual(obj.version, 5)
        # Check determinism
        u2 = uuid.uuid5(uuid.NAMESPACE_DNS, name)
        self.assertEqual(str(u2), u)

    def test_inspect_v1(self):
        u = uuid.uuid1()
        info = self.manager.inspect(str(u))
        self.assertTrue(info["valid"])
        self.assertEqual(info["version"], 1)
        self.assertIn("time", info)
        self.assertIn("mac", info)
        self.assertIn("timestamp_iso", info)

    def test_inspect_invalid(self):
        info = self.manager.inspect("invalid-uuid")
        self.assertFalse(info["valid"])

    def test_validate(self):
        self.assertTrue(self.manager.validate(str(uuid.uuid4())))
        self.assertFalse(self.manager.validate("not-a-uuid"))

    def test_extract_uuids(self):
        u1 = str(uuid.uuid4())
        u2 = str(uuid.uuid1())
        u3 = str(uuid.uuid5(uuid.NAMESPACE_DNS, "test"))

        # Upper and mixed cases
        text = f"Here is {u1.upper()}, and {u2}, also {u3}. Oh and {u1} again! Plus an invalid 12345678-1234-1234-1234-12345678901z"

        uuids = self.manager.extract(text)
        self.assertEqual(len(uuids), 4)
        self.assertEqual(uuids[0], u1.lower())
        self.assertEqual(uuids[1], u2)
        self.assertEqual(uuids[2], u3)
        self.assertEqual(uuids[3], u1)

        unique_uuids = self.manager.extract(text, unique=True)
        self.assertEqual(len(unique_uuids), 3)
        self.assertEqual(unique_uuids, [u1, u2, u3])

if __name__ == '__main__':
    unittest.main()
