import unittest
from unittest.mock import MagicMock, patch, call
from pathlib import Path
from shared.image_lab import ImageLabManager

class TestImageLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = ImageLabManager()

    @patch("shared.image_lab.HAS_PIL", True)
    @patch("shared.image_lab.Image")
    def test_get_info(self, mock_image):
        mock_img_instance = MagicMock()
        mock_img_instance.format = "JPEG"
        mock_img_instance.mode = "RGB"
        mock_img_instance.width = 800
        mock_img_instance.height = 600
        mock_img_instance.info = {"dpi": 72}

        # Configure context manager
        mock_image.open.return_value.__enter__.return_value = mock_img_instance

        with patch.object(Path, "exists", return_value=True):
            info = self.manager.get_info(Path("test.jpg"))

            self.assertEqual(info["filename"], "test.jpg")
            self.assertEqual(info["format"], "JPEG")
            self.assertEqual(info["mode"], "RGB")
            self.assertEqual(info["width"], 800)
            self.assertEqual(info["height"], 600)

    @patch("shared.image_lab.HAS_PIL", True)
    @patch("shared.image_lab.Image")
    def test_convert(self, mock_image):
        mock_img_instance = MagicMock()
        mock_image.open.return_value.__enter__.return_value = mock_img_instance

        input_path = Path("test.png")
        output_path = Path("test.jpg")

        with patch.object(Path, "exists", return_value=True):
            self.manager.convert(input_path, output_path, quality=90)

            mock_image.open.assert_called_with(input_path)
            # Ensure saved with JPG format inferred from extension
            mock_img_instance.save.assert_called_with(output_path, format="JPG", quality=90)

    @patch("shared.image_lab.HAS_PIL", True)
    @patch("shared.image_lab.Image")
    def test_convert_default(self, mock_image):
        mock_img_instance = MagicMock()
        mock_image.open.return_value.__enter__.return_value = mock_img_instance

        input_path = Path("test.png")
        output_path = Path("test.jpg")

        with patch.object(Path, "exists", return_value=True):
            # Test with None quality (default)
            self.manager.convert(input_path, output_path, quality=None)

            mock_image.open.assert_called_with(input_path)
            # Ensure saved without quality argument
            mock_img_instance.save.assert_called_with(output_path, format="JPG")

    @patch("shared.image_lab.HAS_PIL", True)
    @patch("shared.image_lab.Image")
    def test_resize_maintain_aspect(self, mock_image):
        mock_img_instance = MagicMock()
        mock_img_instance.size = (1000, 800)
        mock_image.open.return_value.__enter__.return_value = mock_img_instance

        input_path = Path("test.jpg")
        output_path = Path("resized.jpg")

        with patch.object(Path, "exists", return_value=True):
            # Resize width to 500 (half)
            self.manager.resize(input_path, output_path, width=500, height=None)

            # Expected height is 400
            mock_img_instance.resize.assert_called()
            args, _ = mock_img_instance.resize.call_args
            self.assertEqual(args[0], (500, 400))
            mock_img_instance.resize.return_value.save.assert_called_with(output_path)

    @patch("shared.image_lab.HAS_PIL", True)
    @patch("shared.image_lab.Image")
    def test_resize_no_aspect(self, mock_image):
        mock_img_instance = MagicMock()
        mock_img_instance.size = (1000, 800)
        mock_image.open.return_value.__enter__.return_value = mock_img_instance

        input_path = Path("test.jpg")
        output_path = Path("resized.jpg")

        with patch.object(Path, "exists", return_value=True):
            self.manager.resize(input_path, output_path, width=500, height=500, maintain_aspect=False)

            args, _ = mock_img_instance.resize.call_args
            self.assertEqual(args[0], (500, 500))

    @patch("shared.image_lab.HAS_PIL", True)
    @patch("shared.image_lab.Image")
    @patch("shared.image_lab.ImageDraw")
    @patch("shared.image_lab.ImageFont")
    def test_create_placeholder(self, mock_font, mock_draw, mock_image):
        mock_img_instance = MagicMock()
        mock_image.new.return_value = mock_img_instance

        mock_draw_instance = MagicMock()
        mock_draw.Draw.return_value = mock_draw_instance

        # Mock textbbox return value (left, top, right, bottom)
        mock_draw_instance.textbbox.return_value = (0, 0, 100, 20)

        output_path = Path("placeholder.png")

        self.manager.create_placeholder(output_path, 400, 300, color="blue", text="Hello")

        mock_image.new.assert_called_with("RGB", (400, 300), "blue")
        mock_draw_instance.text.assert_called()
        mock_img_instance.save.assert_called_with(output_path)

    @patch("shared.image_lab.HAS_PIL", False)
    def test_missing_pil_dependency(self):
        with self.assertRaises(ImportError) as context:
            # We bypass _check_pil on init, but call it on methods
            # However, since _check_pil checks the global HAS_PIL which we patched...
            self.manager.get_info(Path("test.jpg"))

        self.assertIn("pip install Pillow", str(context.exception))

    @patch("shared.image_lab.HAS_PIL", True)
    @patch("shared.image_lab.Image")
    def test_hide_message(self, mock_image):
        # Mock input image
        mock_input_img = MagicMock()
        mock_input_img.size = (10, 1) # 10 pixels -> 30 values -> 30 bits capacity
        mock_input_img.mode = "RGB"
        # 10 pixels: (100, 100, 100)
        mock_input_img.getdata.return_value = [(100, 100, 100)] * 10

        # Make convert return self so attributes are preserved
        mock_input_img.convert.return_value = mock_input_img

        # Mock output image
        mock_output_img = MagicMock()
        mock_image.new.return_value = mock_output_img

        mock_image.open.return_value.__enter__.return_value = mock_input_img

        input_path = Path("input.png")
        output_path = Path("output.png")
        message = "A" # 'A' -> 65 -> 01000001. Plus null terminator (00000000). Total 16 bits.
        # 16 bits < 30 bits capacity. OK.

        with patch.object(Path, "exists", return_value=True):
            self.manager.hide_message(input_path, output_path, message)

            mock_image.open.assert_called_with(input_path)
            mock_input_img.convert.assert_called_with("RGB")

            # Verify putdata was called with modified pixels
            mock_output_img.putdata.assert_called()
            args, _ = mock_output_img.putdata.call_args
            new_pixels = args[0]

            # Verify first few pixels match the message 'A' + null
            # 'A' = 01000001
            # \0  = 00000000
            # Total bits: 0100000100000000

            # Pixel 0: (100, 100, 100) -> 01100100 (binary 100)
            # Bits to hide: 0, 1, 0
            # R: 100 -> LSB 0 -> 100 (even)
            # G: 100 -> LSB 1 -> 101 (odd)
            # B: 100 -> LSB 0 -> 100 (even)
            self.assertEqual(new_pixels[0], (100, 101, 100))

            # Pixel 1: bits 0, 0, 0
            self.assertEqual(new_pixels[1], (100, 100, 100))

            # Pixel 2: bits 0, 1, 0
            self.assertEqual(new_pixels[2], (100, 101, 100))

            mock_output_img.save.assert_called_with(output_path, "PNG")

    @patch("shared.image_lab.HAS_PIL", True)
    @patch("shared.image_lab.Image")
    def test_reveal_message(self, mock_image):
        mock_input_img = MagicMock()
        mock_input_img.size = (10, 1)
        # Make convert return self so getdata works
        mock_input_img.convert.return_value = mock_input_img

        # Construct pixels that hide "Hi"
        # H: 01001000
        # i: 01101001
        # \0: 00000000
        # Total bits: 01001000 01101001 00000000
        bits = "010010000110100100000000"
        pixels = []
        for i in range(0, len(bits), 3):
            chunk = bits[i:i+3]
            # pad chunk with 0 if needed (though logic handles exact match)
            while len(chunk) < 3: chunk += "0"

            r = 100 | int(chunk[0])
            g = 100 | int(chunk[1])
            b = 100 | int(chunk[2])
            pixels.append((r, g, b))

        mock_input_img.getdata.return_value = pixels
        mock_image.open.return_value.__enter__.return_value = mock_input_img

        input_path = Path("secret.png")

        with patch.object(Path, "exists", return_value=True):
            revealed = self.manager.reveal_message(input_path)
            self.assertEqual(revealed, "Hi")

    @patch("shared.image_lab.HAS_PIL", True)
    @patch("shared.image_lab.Image")
    def test_hide_message_capacity_error(self, mock_image):
        mock_input_img = MagicMock()
        mock_input_img.size = (1, 1) # 1 pixel = 3 bits
        # Make convert return self
        mock_input_img.convert.return_value = mock_input_img
        mock_input_img.getdata.return_value = [(100, 100, 100)]

        mock_image.open.return_value.__enter__.return_value = mock_input_img

        input_path = Path("small.png")
        output_path = Path("out.png")
        message = "Too long"

        with patch.object(Path, "exists", return_value=True):
            with self.assertRaises(ValueError) as context:
                self.manager.hide_message(input_path, output_path, message)

            self.assertIn("too small", str(context.exception))

    @patch("shared.image_lab.HAS_PIL", True)
    @patch("shared.image_lab.Image")
    def test_hide_message_utf8(self, mock_image):
        # Mock input image
        mock_input_img = MagicMock()
        mock_input_img.size = (20, 1) # Enough space
        mock_input_img.mode = "RGB"
        mock_input_img.getdata.return_value = [(100, 100, 100)] * 20

        # Make convert return self
        mock_input_img.convert.return_value = mock_input_img

        # Mock output image
        mock_output_img = MagicMock()
        mock_image.new.return_value = mock_output_img

        mock_image.open.return_value.__enter__.return_value = mock_input_img

        input_path = Path("input.png")
        output_path = Path("output.png")
        message = "ñ" # 2 bytes in UTF-8: 0xC3 0xB1 -> 11000011 10110001. + null (00000000)

        with patch.object(Path, "exists", return_value=True):
            self.manager.hide_message(input_path, output_path, message)

            mock_output_img.putdata.assert_called()
            args, _ = mock_output_img.putdata.call_args
            new_pixels = args[0]

            # Verify bits
            # Byte 1: 11000011
            # Pixel 0 (3 bits): 1 1 0 -> (101, 101, 100)
            self.assertEqual(new_pixels[0], (101, 101, 100))
            # Pixel 1 (3 bits): 0 0 0 -> (100, 100, 100)
            self.assertEqual(new_pixels[1], (100, 100, 100))
            # Pixel 2 (2 bits from Byte 1): 1 1 -> (101, 101, 100) <- wait, rest is from byte 2

            # Bits: 110 000 11 1 011 000 1 ...
            # P0: 110
            # P1: 000
            # P2: 11 1  (1 from byte 2 start) -> (101, 101, 101)

            self.assertEqual(new_pixels[2], (101, 101, 101))

if __name__ == "__main__":
    unittest.main()
