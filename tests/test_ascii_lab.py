import unittest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
import sys

# Mock Pillow before importing AsciiLabManager
sys.modules['PIL'] = MagicMock()
sys.modules['PIL.Image'] = MagicMock()
sys.modules['PIL.ImageSequence'] = MagicMock()

from shared.ascii_lab import AsciiLabManager

class TestAsciiLab(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.manager = AsciiLabManager()
        # Mock Path.exists to always return True for tests
        self.patcher = patch('pathlib.Path.exists', return_value=True)
        self.mock_exists = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    @patch('shared.ascii_lab.Image.open')
    def test_convert_image_to_ascii(self, mock_open):
        # Mock Image object
        mock_img = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_img

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
        # 100x50 pixels (since aspect ratio correction applies)
        # width=100
        # height = 100 * (100/100) * 0.5 = 50

        mock_gray.getdata.return_value = [0, 255] * 2500 # 5000 pixels

        result = self.manager.convert_image_to_ascii(Path("test.png"), width=100)

        self.assertTrue(len(result) > 0)
        self.assertIn("@", result) # Should match 0
        self.assertIn(" ", result) # Should match 255 (if space is last char)

    @patch('shared.ascii_lab.Image.open')
    @patch('shared.ascii_lab.ImageSequence.Iterator')
    @patch('time.sleep')
    @patch('builtins.print')
    def test_play_gif(self, mock_print, mock_sleep, mock_iterator, mock_open):
        # Mock Image object
        mock_img = MagicMock()
        mock_img.is_animated = True
        mock_open.return_value.__enter__.return_value = mock_img

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

        mock_iterator.return_value = [frame1, frame2]

        # Mock sleep to raise exception to break infinite loop
        mock_sleep.side_effect = KeyboardInterrupt

        self.manager.play_gif(Path("test.gif"), width=10)

        # Verify print was called (clearing screen and printing frame)
        self.assertTrue(mock_print.called)
        # Verify sleep was called
        self.assertTrue(mock_sleep.called)



    def test_generate_text_banner(self):
        result = self.manager.generate_text_banner("HI", char="*")
        lines = result.split("\n")
        self.assertEqual(len(lines), 5)
        self.assertTrue(lines[0].startswith("*   *"))

    def test_generate_ascii_table(self):
        result = self.manager.generate_ascii_table()
        self.assertIn("Dec   | Hex   | Oct   | Char", result)
        self.assertIn("NUL (null)", result)
        self.assertIn("65    | 0x41  | 0o101 | A", result)

    async def test_tui_ascii_text_and_table(self):
        from textual.app import App
        from shared.tui_ascii import AsciiLabTab
        from textual.widgets import TabbedContent
        from pathlib import Path

        class DummyApp(App):
            def compose(self):
                yield AsciiLabTab(Path("."))

        app = DummyApp()
        async with app.run_test() as pilot:
            # Must activate tab
            app.query_one(TabbedContent).active = "tab-2" # Text Banner
            await pilot.pause()

            app.query_one("#ascii-text-input").value = "TEST"

            # Use action or call directly
            tab = app.query_one(AsciiLabTab)
            tab.on_text_gen()

            output_static = app.query_one("#ascii-text-output")
            self.assertIn("#####", str(output_static.render()))

            # Table test
            tab.on_table_load()
            table_static = app.query_one("#ascii-table-output")
            self.assertIn("0x41", str(table_static.render()))

if __name__ == '__main__':
    unittest.main()