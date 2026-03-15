import unittest
from unittest.mock import patch
import argparse
from shared.cbor_lab import CborManager, run_cbor_lab_logic

class TestCborManager(unittest.TestCase):
    def setUp(self):
        self.manager = CborManager()

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
        # A string that will definitely throw a CBORDecodeError or ValueError
        # CBOR requires valid structure, b"\x1c" is float16 but missing 2 bytes
        with self.assertRaises(ValueError):
            self.manager.decode(b"\x1c")

class TestCborLabLogic(unittest.TestCase):
    @patch('sys.stdout')
    def test_run_cbor_lab_encode(self, mock_stdout):
        args = argparse.Namespace(action='encode', input='{"a": 1}', hex=True)
        result = run_cbor_lab_logic(args)
        self.assertTrue(result)

    @patch('sys.stdout')
    def test_run_cbor_lab_decode(self, mock_stdout):
        import cbor2
        encoded = cbor2.dumps({"a": 1})
        args = argparse.Namespace(action='decode', input=encoded.hex())
        result = run_cbor_lab_logic(args)
        self.assertTrue(result)

    @patch('sys.stderr')
    def test_run_cbor_lab_invalid_json(self, mock_stderr):
        args = argparse.Namespace(action='encode', input='{"a": 1', hex=True)
        result = run_cbor_lab_logic(args)
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
