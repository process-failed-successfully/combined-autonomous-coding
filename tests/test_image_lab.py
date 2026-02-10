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

if __name__ == "__main__":
    unittest.main()
