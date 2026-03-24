import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add mock PIL.Image directly to sys.modules BEFORE importing the module
import sys
if 'PIL' not in sys.modules:
    sys.modules['PIL'] = MagicMock()
if 'PIL.Image' not in sys.modules:
    sys.modules['PIL.Image'] = MagicMock()
if 'PIL.ExifTags' not in sys.modules:
    sys.modules['PIL.ExifTags'] = MagicMock()
    sys.modules['PIL.ExifTags'].TAGS = {271: 'Make', 272: 'Model'}

from shared.exif_lab import ExifManager
import shared.exif_lab

class TestExifLab(unittest.TestCase):
    def setUp(self):
        self.manager = ExifManager(Path("."))

        # Ensure MagicMock on the module attributes
        if not hasattr(shared.exif_lab, 'Image'):
            shared.exif_lab.Image = MagicMock()
        if not hasattr(shared.exif_lab, 'TAGS'):
            shared.exif_lab.TAGS = {271: 'Make', 272: 'Model'}

    @patch("shared.exif_lab.HAS_PIL", True)
    @patch("shared.exif_lab.Image")
    def test_read_exif(self, mock_image):
        mock_img = MagicMock()
        mock_img.getexif.return_value = {271: 'Canon', 272: 'EOS 80D', 999: 'Unknown'}
        mock_image.open.return_value.__enter__.return_value = mock_img

        input_path = Path("input.jpg")

        with patch.object(Path, "exists", return_value=True):
            result = self.manager.read(input_path)

            # The real read method uses TAGS from ExifTags
            self.assertEqual(result, {'Make': 'Canon', 'Model': 'EOS 80D', 999: 'Unknown'})
            mock_image.open.assert_called_with(input_path)

    @patch("shared.exif_lab.HAS_PIL", True)
    @patch("shared.exif_lab.Image")
    def test_read_exif_no_data(self, mock_image):
        mock_img = MagicMock()
        mock_img.getexif.return_value = None
        mock_image.open.return_value.__enter__.return_value = mock_img

        input_path = Path("input.jpg")

        with patch.object(Path, "exists", return_value=True):
            result = self.manager.read(input_path)

            self.assertEqual(result, {})

    @patch("shared.exif_lab.HAS_PIL", True)
    @patch("shared.exif_lab.Image")
    def test_remove_exif(self, mock_image):
        mock_img = MagicMock()
        mock_img.mode = "RGB"
        mock_img.size = (100, 100)
        mock_img.format = "JPEG"
        mock_image.open.return_value.__enter__.return_value = mock_img

        mock_new_img = MagicMock()
        mock_image.new.return_value = mock_new_img

        input_path = Path("input.jpg")
        output_path = Path("output.jpg")

        with patch.object(Path, "exists", return_value=True):
            result = self.manager.remove(input_path, output_path)

            self.assertEqual(result, output_path)
            mock_image.open.assert_called_with(input_path)
            mock_image.new.assert_called_with("RGB", (100, 100))
            mock_new_img.paste.assert_called_with(mock_img)
            mock_new_img.save.assert_called_with(output_path, format="JPEG", exif=b"")

    @patch("shared.exif_lab.HAS_PIL", False)
    def test_missing_pil(self):
        with self.assertRaises(ImportError):
            self.manager.read(Path("test.jpg"))

if __name__ == "__main__":
    unittest.main()
