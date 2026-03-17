import unittest
from unittest.mock import patch
import argparse
from shared.bson_lab import BsonManager, run_bson_lab_logic

class TestBsonManager(unittest.TestCase):
    def setUp(self):
        self.manager = BsonManager()

    def test_encode_decode(self):
        original = {"test": 123, "list": [1, 2, 3], "string": "hello"}
        encoded = self.manager.encode(original)
        self.assertIsInstance(encoded, bytes)
        decoded = self.manager.decode(encoded)
        self.assertEqual(original, decoded)

    def test_encode_invalid(self):
        with self.assertRaises(TypeError):
            self.manager.encode(object())

    def test_decode_invalid(self):
        # A string that will definitely throw a ValueError
        with self.assertRaises(ValueError):
            self.manager.decode(b"invalid")

class TestBsonLabLogic(unittest.TestCase):
    @patch('sys.stdout')
    def test_run_bson_lab_encode(self, mock_stdout):
        args = argparse.Namespace(action='encode', input='{"a": 1}', hex=True)
        result = run_bson_lab_logic(args)
        self.assertTrue(result)

    @patch('sys.stdout')
    def test_run_bson_lab_decode(self, mock_stdout):
        import bson
        encoded = bson.dumps({"a": 1})
        args = argparse.Namespace(action='decode', input=encoded.hex())
        result = run_bson_lab_logic(args)
        self.assertTrue(result)

    @patch('sys.stderr')
    def test_run_bson_lab_invalid_json(self, mock_stderr):
        args = argparse.Namespace(action='encode', input='{"a": 1', hex=True)
        result = run_bson_lab_logic(args)
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
