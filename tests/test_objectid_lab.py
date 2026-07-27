import unittest
from unittest.mock import patch
import sys
from io import StringIO
import argparse
from shared.objectid_lab import ObjectIdLabManager, run_objectid_lab_logic

class TestObjectIdLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = ObjectIdLabManager()

    def test_generate(self):
        result = self.manager.generate(count=2)
        self.assertEqual(len(result), 2)
        for oid in result:
            self.assertEqual(len(oid), 24)
            self.assertTrue(self.manager.inspect(oid)["valid"])

    def test_inspect_valid(self):
        oid = self.manager.generate(count=1)[0]
        info = self.manager.inspect(oid)
        self.assertTrue(info["valid"])
        self.assertEqual(info["objectid"], oid)
        self.assertIn("generation_time", info)

    def test_inspect_invalid(self):
        info = self.manager.inspect("invalid_oid")
        self.assertFalse(info["valid"])
        self.assertIn("Invalid ObjectId format", info["error"])

    def test_extract(self):
        oid1 = self.manager.generate(count=1)[0]
        oid2 = self.manager.generate(count=1)[0]
        text = f"Here is one {oid1} and another {oid2} and {oid1} again."

        extracted = self.manager.extract(text)
        self.assertEqual(len(extracted), 3)
        self.assertEqual(extracted[0], oid1)
        self.assertEqual(extracted[1], oid2)
        self.assertEqual(extracted[2], oid1)

        extracted_unique = self.manager.extract(text, unique=True)
        self.assertEqual(len(extracted_unique), 2)
        self.assertEqual(extracted_unique[0], oid1)
        self.assertEqual(extracted_unique[1], oid2)

class TestObjectIdLabCLI(unittest.TestCase):
    def setUp(self):
        self.manager = ObjectIdLabManager()
        self.held_stdout = StringIO()
        self.held_stderr = StringIO()
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        sys.stdout = self.held_stdout
        sys.stderr = self.held_stderr

    def tearDown(self):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr

    def test_cli_generate(self):
        args = argparse.Namespace(action="generate", count=2)
        success = run_objectid_lab_logic(args)
        self.assertTrue(success)
        output = self.held_stdout.getvalue().strip().split('\n')
        self.assertEqual(len(output), 2)
        for oid in output:
            self.assertEqual(len(oid), 24)

    def test_cli_inspect(self):
        oid = self.manager.generate()[0]
        args = argparse.Namespace(action="inspect", objectid=oid)
        success = run_objectid_lab_logic(args)
        self.assertTrue(success)
        output = self.held_stdout.getvalue()
        self.assertIn("ObjectId Inspection:", output)
        self.assertIn("Valid:           True", output)
        self.assertIn("Generation Time:", output)

    def test_cli_extract(self):
        oid = self.manager.generate()[0]
        args = argparse.Namespace(action="extract", text=f"id: {oid}", unique=False)
        success = run_objectid_lab_logic(args)
        self.assertTrue(success)
        output = self.held_stdout.getvalue().strip()
        self.assertEqual(output, oid)

if __name__ == '__main__':
    unittest.main()
