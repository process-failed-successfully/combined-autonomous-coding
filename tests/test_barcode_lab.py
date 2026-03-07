import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import os
import tempfile
import shutil
import sys

# Ensure shared is importable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.barcode_lab import BarcodeLabManager, run_barcode_lab_logic  # noqa: E402

class TestBarcodeLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = BarcodeLabManager()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_list_formats(self):
        formats = self.manager.list_formats()
        self.assertIn("code128", formats)
        self.assertIn("ean13", formats)

    def test_validate_valid_data(self):
        self.assertTrue(self.manager.validate("123456789012", "ean13"))
        self.assertTrue(self.manager.validate("hello", "code128"))

    def test_validate_invalid_data(self):
        # EAN13 must be digits
        self.assertFalse(self.manager.validate("hello", "ean13"))
        # Invalid format name
        self.assertFalse(self.manager.validate("123", "invalid_format"))

    def test_generate_svg(self):
        output_path = Path(self.temp_dir) / "test_barcode"
        result = self.manager.generate("hello", fmt="code128", output_path=output_path, svg=True)
        self.assertIn("test_barcode", result)

        # check file created
        self.assertTrue((Path(self.temp_dir) / "test_barcode.svg").exists())

    def test_generate_png(self):
        output_path = Path(self.temp_dir) / "test_barcode"
        result = self.manager.generate("hello", fmt="code128", output_path=output_path, svg=False)
        self.assertIn("test_barcode", result)

        # check file created
        self.assertTrue((Path(self.temp_dir) / "test_barcode.png").exists())

    def test_generate_invalid_format(self):
        with self.assertRaises(ValueError):
            self.manager.generate("hello", fmt="invalid_format")


class TestBarcodeLabCLI(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    @patch("builtins.print")
    def test_cli_list(self, mock_print):
        args = MagicMock()
        args.action = "list"
        success = run_barcode_lab_logic(args)
        self.assertTrue(success)
        mock_print.assert_any_call("Supported Barcode Formats:")

    @patch("builtins.print")
    def test_cli_validate_success(self, mock_print):
        args = MagicMock()
        args.action = "validate"
        args.data = "hello"
        args.format = "code128"
        success = run_barcode_lab_logic(args)
        self.assertTrue(success)
        self.assertIn("✅", mock_print.call_args[0][0])

    @patch("builtins.print")
    def test_cli_validate_fail(self, mock_print):
        args = MagicMock()
        args.action = "validate"
        args.data = "hello"
        args.format = "ean13"
        success = run_barcode_lab_logic(args)
        self.assertFalse(success)
        self.assertIn("❌", mock_print.call_args[0][0])

    @patch("builtins.print")
    def test_cli_generate_missing_data(self, mock_print):
        args = MagicMock()
        args.action = "generate"
        args.data = None
        success = run_barcode_lab_logic(args)
        self.assertFalse(success)

    @patch("builtins.print")
    def test_cli_generate_success(self, mock_print):
        args = MagicMock()
        args.action = "generate"
        args.data = "hello"
        args.format = "code128"
        args.svg = True
        args.output = str(Path(self.temp_dir) / "out")
        success = run_barcode_lab_logic(args)
        self.assertTrue(success)
        self.assertTrue((Path(self.temp_dir) / "out.svg").exists())

if __name__ == "__main__":
    unittest.main()
