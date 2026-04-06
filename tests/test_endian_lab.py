import unittest
import argparse
import io
from unittest.mock import patch
from shared.endian_lab import EndianManager, run_endian_lab_logic

class TestEndianManager(unittest.TestCase):
    def setUp(self):
        self.manager = EndianManager()

    def test_convert_hex_simple(self):
        self.assertEqual(self.manager.convert_hex("11223344"), "44332211")

    def test_convert_hex_with_prefix(self):
        self.assertEqual(self.manager.convert_hex("0x11223344"), "44332211")

    def test_convert_hex_with_spaces(self):
        self.assertEqual(self.manager.convert_hex("11 22 33 44"), "44332211")

    def test_convert_hex_invalid_length(self):
        with self.assertRaises(ValueError):
            self.manager.convert_hex("112")

    def test_convert_int_16bit(self):
        # 0x1234 -> 4660. Swapped: 0x3412 -> 13330
        self.assertEqual(self.manager.convert_int(4660, 2), 13330)

    def test_convert_int_32bit(self):
        # 0x11223344 -> 287454020. Swapped: 0x44332211 -> 1144201745
        self.assertEqual(self.manager.convert_int(287454020, 4), 1144201745)

    def test_convert_int_invalid_size(self):
        with self.assertRaises(ValueError):
            self.manager.convert_int(287454020, 3)

class TestEndianLabLogic(unittest.TestCase):
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_hex(self, mock_stdout):
        args = argparse.Namespace(action="hex", value="aabbccdd")
        self.assertTrue(run_endian_lab_logic(args))
        self.assertEqual(mock_stdout.getvalue().strip(), "ddccbbaa")

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_int(self, mock_stdout):
        args = argparse.Namespace(action="int", value="4660", size="2")
        self.assertTrue(run_endian_lab_logic(args))
        self.assertEqual(mock_stdout.getvalue().strip(), "13330")

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_run_hex_missing_val(self, mock_stderr):
        args = argparse.Namespace(action="hex", value=None)
        self.assertFalse(run_endian_lab_logic(args))

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_run_int_missing_val(self, mock_stderr):
        args = argparse.Namespace(action="int", value=None, size="2")
        self.assertFalse(run_endian_lab_logic(args))

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_run_invalid_action(self, mock_stderr):
        args = argparse.Namespace(action="foo")
        self.assertFalse(run_endian_lab_logic(args))

if __name__ == '__main__':
    unittest.main()
