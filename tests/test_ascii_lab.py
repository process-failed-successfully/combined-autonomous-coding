import unittest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
import sys

# Removed global sys.modules patching for PIL

from shared.ascii_lab import AsciiLabManager

class TestAsciiLab(unittest.TestCase):
    def setUp(self):
        self.manager = AsciiLabManager()
        # Mock Path.exists to always return True for tests
        self.patcher = patch('pathlib.Path.exists', return_value=True)
        self.mock_exists = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_convert_image_to_ascii(self):
        with patch('shared.ascii_lab.HAS_PIL', True), \
             patch('shared.ascii_lab.Image') as mock_image:

            # Mock Image object
            mock_img = MagicMock()
            mock_image.open.return_value.__enter__.return_value = mock_img

            # Setup image properties
            mock_img.width = 100
            mock_img.height = 100

            # Mock resized image
            mock_resized = MagicMock()
            mock_img.resize.return_value = mock_resized

            # Mock grayscale image
            mock_gray = MagicMock()
            mock_resized.convert.return_value = mock_gray

            # Mock pixel data (simple gradient)
            mock_gray.getdata.return_value = [0, 255] * 2500 # 5000 pixels

            result = self.manager.convert_image_to_ascii(Path("test.png"), width=100)

            self.assertTrue(len(result) > 0)
            self.assertIn("@", result) # Should match 0
            self.assertIn(" ", result) # Should match 255

    def test_play_gif(self):
        with patch('shared.ascii_lab.HAS_PIL', True), \
             patch('shared.ascii_lab.Image') as mock_image, \
             patch('shared.ascii_lab.ImageSequence') as mock_image_sequence, \
             patch('time.sleep') as mock_sleep, \
             patch('builtins.print') as mock_print:

            # Mock Image object
            mock_img = MagicMock()
            mock_img.is_animated = True
            mock_image.open.return_value.__enter__.return_value = mock_img

            # Mock Iterator to return a few frames
            frame1 = MagicMock()
            frame1.width = 10
            frame1.height = 10
            frame1.info = {'duration': 100}
            frame1.resize.return_value.convert.return_value.getdata.return_value = [0]*50

            frame2 = MagicMock()
            frame2.width = 10
            frame2.height = 10
            frame2.info = {'duration': 100}
            frame2.resize.return_value.convert.return_value.getdata.return_value = [255]*50

            # mock_image_sequence.Iterator should return the list of frames
            mock_image_sequence.Iterator.return_value = [frame1, frame2]

            # Mock sleep to raise exception to break infinite loop
            mock_sleep.side_effect = KeyboardInterrupt

            self.manager.play_gif(Path("test.gif"), width=10)

            # Verify print was called
            self.assertTrue(mock_print.called)
            # Verify sleep was called
            self.assertTrue(mock_sleep.called)

if __name__ == '__main__':
    unittest.main()
