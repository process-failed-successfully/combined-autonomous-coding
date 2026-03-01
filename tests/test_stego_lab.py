import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys

# Mock Pillow before importing StegoLabManager
sys.modules['PIL'] = MagicMock()
sys.modules['PIL.Image'] = MagicMock()

from shared.stego_lab import StegoLabManager  # noqa: E402


class TestStegoLab(unittest.TestCase):
    def setUp(self):
        self.manager = StegoLabManager()
        self.patcher = patch('pathlib.Path.exists', return_value=True)
        self.mock_exists = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_str_to_bin_and_back(self):
        original_text = "hello world!"
        binary = self.manager._str_to_bin(original_text)
        decoded_text = self.manager._bin_to_str(binary)
        self.assertEqual(original_text, decoded_text)

        # Test with null terminator
        binary_with_null = binary + '0000000010101010'
        decoded_text_null = self.manager._bin_to_str(binary_with_null)
        self.assertEqual(original_text, decoded_text_null)

    @patch('shared.stego_lab.Image.open')
    def test_encode_decode(self, mock_open):
        # We need a realistic mock for an image that we can set and get pixels from.
        # Since Steganography involves mutating and reading pixel tuples, we create a
        # dummy implementation.

        class MockPixelAccess:
            def __init__(self, w, h):
                # Init with black pixels
                self.pixels = [[(0, 0, 0, 255) for _ in range(h)] for _ in range(w)]

            def __getitem__(self, xy):
                x, y = xy
                return self.pixels[x][y]

            def __setitem__(self, xy, val):
                x, y = xy
                self.pixels[x][y] = val

        class MockImage:
            def __init__(self, w, h):
                self.width = w
                self.height = h
                self.size = (w, h)
                self.pixel_access = MockPixelAccess(w, h)

            def convert(self, mode):
                # Ignore mode
                return self

            def load(self):
                return self.pixel_access

            def save(self, output_path, format):
                pass

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                pass

        # 10x10 image = 100 pixels = 400 channels (bits)
        # We can hide 400/8 = 50 characters, plenty for "secret"
        mock_img_instance = MockImage(10, 10)
        mock_open.return_value = mock_img_instance

        secret_text = "top secret 123"

        # Encode
        result = self.manager.encode(Path("input.png"), secret_text, Path("output.png"))
        self.assertTrue(result)

        # Decode
        extracted_text = self.manager.decode(Path("output.png"))
        self.assertEqual(secret_text, extracted_text)

    @patch('shared.stego_lab.Image.open')
    def test_encode_too_large(self, mock_open):
        class MockImage:
            def __init__(self):
                self.size = (1, 1)  # Only 4 channels = 4 bits capacity

            def convert(self, mode):
                return self

            def load(self):
                return None

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                pass

        mock_open.return_value = MockImage()

        with self.assertRaises(ValueError) as context:
            self.manager.encode(Path("input.png"), "A", Path("output.png"))

        self.assertIn("Text is too large to hide in this image", str(context.exception))


if __name__ == '__main__':
    unittest.main()
