import unittest
from shared.size_lab import parse_size, format_size
import argparse
from shared.size_lab import run_size_lab_logic
import io
import sys

class TestSizeLab(unittest.TestCase):

    def test_parse_size_valid_iec(self):
        res = parse_size("2 KiB")
        self.assertTrue(res["success"])
        self.assertEqual(res["bytes"], 2048)

        res = parse_size("1.5 MiB")
        self.assertTrue(res["success"])
        self.assertEqual(res["bytes"], int(1.5 * 1024 * 1024))

    def test_parse_size_valid_si(self):
        res = parse_size("2 KB")
        self.assertTrue(res["success"])
        self.assertEqual(res["bytes"], 2000)

        res = parse_size("1.5 GB")
        self.assertTrue(res["success"])
        self.assertEqual(res["bytes"], int(1.5 * 1000**3))

    def test_parse_size_no_unit(self):
        res = parse_size("1024")
        self.assertTrue(res["success"])
        self.assertEqual(res["bytes"], 1024)

    def test_parse_size_invalid(self):
        res = parse_size("invalid")
        self.assertFalse(res["success"])
        self.assertIn("Invalid format", res["error"])

        res = parse_size("1.5.5 GB")
        self.assertFalse(res["success"])

        res = parse_size("1.5 ZX")
        self.assertFalse(res["success"])
        self.assertIn("Unknown unit", res["error"])

    def test_format_size_iec(self):
        res = format_size(1024)
        self.assertTrue(res["success"])
        self.assertEqual(res["formatted"], "1.00 KiB")

        res = format_size(1048576)
        self.assertTrue(res["success"])
        self.assertEqual(res["formatted"], "1.00 MiB")

        res = format_size(1500 * 1024 * 1024)
        self.assertTrue(res["success"])
        self.assertEqual(res["formatted"], "1.46 GiB")

    def test_format_size_si(self):
        res = format_size(1000, use_iec=False)
        self.assertTrue(res["success"])
        self.assertEqual(res["formatted"], "1.00 KB")

        res = format_size(1500000000, use_iec=False)
        self.assertTrue(res["success"])
        self.assertEqual(res["formatted"], "1.50 GB")

    def test_format_size_edge_cases(self):
        res = format_size(0)
        self.assertTrue(res["success"])
        self.assertEqual(res["formatted"], "0 B")

        res = format_size(-100)
        self.assertFalse(res["success"])
        self.assertIn("negative", res["error"])

        res = format_size(10)
        self.assertTrue(res["success"])
        self.assertEqual(res["formatted"], "10 B")

    def test_cli_parse(self):
        args = argparse.Namespace(action="parse", size="2 KiB")
        capturedOutput = io.StringIO()
        sys.stdout = capturedOutput
        success = run_size_lab_logic(args)
        sys.stdout = sys.__stdout__
        self.assertTrue(success)
        self.assertIn("2048", capturedOutput.getvalue())

    def test_cli_format(self):
        args = argparse.Namespace(action="format", bytes="2048", si=False)
        capturedOutput = io.StringIO()
        sys.stdout = capturedOutput
        success = run_size_lab_logic(args)
        sys.stdout = sys.__stdout__
        self.assertTrue(success)
        self.assertIn("2.00 KiB", capturedOutput.getvalue())

if __name__ == '__main__':
    unittest.main()
