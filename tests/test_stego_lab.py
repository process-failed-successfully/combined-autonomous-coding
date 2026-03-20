import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

from shared.stego_lab import StegoManager


class TestStegoLab(unittest.TestCase):
    def setUp(self):
        self.manager = StegoManager(Path("."))

    @patch("shared.stego_lab.HAS_PIL", True)
    @patch("shared.stego_lab.Image")
    def test_hide_message(self, mock_image):
        mock_img = MagicMock()
        mock_img.size = (10, 1)  # 10 pixels = 30 bits
        mock_img.convert.return_value = mock_img

        # We need mock_img.load() to return a dictionary-like object
        # because the implementation does `pixel_access[x, y] = (r, g, b)`
        pixels = {}
        for i in range(10):
            pixels[(i, 0)] = (100, 100, 100)

        mock_img.load.return_value = pixels
        mock_image.open.return_value.__enter__.return_value = mock_img

        input_path = Path("input.png")
        output_path = Path("output.png")
        message = "A"  # 8 bits + 8 bits null = 16 bits

        with patch.object(Path, "exists", return_value=True):
            result = self.manager.hide(input_path, output_path, message)

            self.assertEqual(result, output_path)
            mock_image.open.assert_called_with(input_path)
            mock_img.save.assert_called_with(output_path, "PNG")

            # Let's verify pixel data was modified
            # 'A' = 01000001
            # null = 00000000
            # bits: 0 1 0 0 0 0 0 1 0 0 0 0 0 0 0 0
            self.assertEqual(pixels[(0, 0)], (100, 101, 100))  # 0, 1, 0
            self.assertEqual(pixels[(1, 0)], (100, 100, 100))  # 0, 0, 0
            self.assertEqual(pixels[(2, 0)], (100, 101, 100))  # 0, 1, 0
            self.assertEqual(pixels[(3, 0)], (100, 100, 100))  # 0, 0, 0

    @patch("shared.stego_lab.HAS_PIL", True)
    @patch("shared.stego_lab.Image")
    def test_extract_message(self, mock_image):
        mock_img = MagicMock()
        mock_img.size = (10, 1)
        mock_img.convert.return_value = mock_img

        pixels = {}
        bits = "010010000110100100000000"  # "Hi\0"
        idx = 0
        for i in range(10):
            r = 100
            g = 100
            b = 100
            if idx < len(bits):
                r = r | int(bits[idx])
                idx += 1
            if idx < len(bits):
                g = g | int(bits[idx])
                idx += 1
            if idx < len(bits):
                b = b | int(bits[idx])
                idx += 1
            pixels[(i, 0)] = (r, g, b)

        mock_img.load.return_value = pixels
        mock_image.open.return_value.__enter__.return_value = mock_img

        input_path = Path("secret.png")

        with patch.object(Path, "exists", return_value=True):
            result = self.manager.extract(input_path)
            self.assertEqual(result, "Hi")

    @patch("shared.stego_lab.HAS_PIL", False)
    def test_missing_pil(self):
        with self.assertRaises(ImportError):
            self.manager.extract(Path("test.png"))


if __name__ == "__main__":
    unittest.main()
