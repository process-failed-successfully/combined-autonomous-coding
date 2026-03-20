import unittest
import argparse
import sys
import io
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Create a dummy image for testing
try:
    from PIL import Image
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

from shared.stego_lab import StegoManager, run_stego_lab_logic


@unittest.skipIf(not HAS_PILLOW, "Pillow is required for Steganography tests.")
class TestStegoLab(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.input_img_path = os.path.join(self.temp_dir.name, "test_input.png")
        self.output_img_path = os.path.join(self.temp_dir.name, "test_output.png")

        # Create a small RGB image
        img = Image.new('RGB', (50, 50), color='white')
        img.save(self.input_img_path)

        self.manager = StegoManager()

        self.held_stdout = io.StringIO()
        self.held_stderr = io.StringIO()
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        sys.stdout = self.held_stdout
        sys.stderr = self.held_stderr

    def tearDown(self):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        # Clean up temp dir
        import shutil
        shutil.rmtree(self.temp_dir.name)

    def test_encode_decode_length(self):
        length = 42
        encoded = self.manager._encode_length(length)
        self.assertEqual(len(encoded), 32)
        decoded = self.manager._decode_length(encoded)
        self.assertEqual(decoded, length)

    def test_text_to_bin(self):
        text = "Hi"
        # H = 01001000, i = 01101001
        bin_str = self.manager._text_to_bin(text)
        self.assertEqual(bin_str, "0100100001101001")

        extracted = self.manager._bin_to_text(bin_str)
        self.assertEqual(extracted, text)

    def test_hide_and_extract_text(self):
        secret_text = "This is a secret message!"

        # Hide the text
        result = self.manager.hide_text(self.input_img_path, secret_text, self.output_img_path)
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.output_img_path))

        # Extract the text
        extracted = self.manager.extract_text(self.output_img_path)
        self.assertEqual(extracted, secret_text)

    def test_hide_text_too_large(self):
        # Image is 50x50 = 2500 pixels. Each pixel stores 3 bits.
        # Max capacity = 7500 bits.
        # 32 bits for length. Max text bits = 7468 -> max chars = 933
        large_text = "A" * 1000

        with self.assertRaises(ValueError):
            self.manager.hide_text(self.input_img_path, large_text, self.output_img_path)

    def test_run_logic_hide(self):
        args = argparse.Namespace(
            action="hide",
            image=self.input_img_path,
            text="CLI Secret",
            output=self.output_img_path
        )

        success = run_stego_lab_logic(args)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(self.output_img_path))
        self.assertIn("Text successfully hidden", self.held_stdout.getvalue())

    def test_run_logic_extract(self):
        # First hide text using the manager
        self.manager.hide_text(self.input_img_path, "CLI Secret Extract", self.output_img_path)

        args = argparse.Namespace(
            action="extract",
            image=self.output_img_path
        )

        success = run_stego_lab_logic(args)
        self.assertTrue(success)
        self.assertIn("CLI Secret Extract", self.held_stdout.getvalue())

if __name__ == "__main__":
    unittest.main()
