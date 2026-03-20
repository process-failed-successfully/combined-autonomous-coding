import pytest
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from textual.app import App, ComposeResult
from shared.tui_stego import StegoLabTab
from shared.stego_lab import HAS_PILLOW

# Create a dummy app to host the tab
class DummyStegoApp(App[None]):
    def compose(self) -> ComposeResult:
        yield StegoLabTab()

class TestStegoLabTab(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        if not HAS_PILLOW:
            self.skipTest("Pillow not installed.")

        self.temp_dir = tempfile.TemporaryDirectory()
        self.input_img = os.path.join(self.temp_dir.name, "test_input.png")
        self.output_img = os.path.join(self.temp_dir.name, "test_output.png")

        from PIL import Image
        img = Image.new('RGB', (100, 100), color='white')
        img.save(self.input_img)

    def tearDown(self):
        if hasattr(self, 'temp_dir'):
            self.temp_dir.cleanup()

    async def test_stego_tab_hide_text(self):
        app = DummyStegoApp()

        async with app.run_test() as pilot:
            tab = app.query_one(StegoLabTab)

            # Set up mock notifications
            tab.notify = MagicMock()

            # Fill inputs
            input_img_widget = tab.query_one("#stego-hide-img")
            input_out_widget = tab.query_one("#stego-hide-out")
            input_text_widget = tab.query_one("#stego-input-text")

            input_img_widget.value = self.input_img
            input_out_widget.value = self.output_img
            input_text_widget.text = "Hello Hidden World!"

            # Click Hide
            btn = tab.query_one("#btn-stego-hide")
            btn.press()
            await pilot.pause(0.1)

            # Check notification
            tab.notify.assert_called_with(f"Text successfully hidden in '{self.output_img}'.", severity="information")

            # Verify output exists
            self.assertTrue(os.path.exists(self.output_img))

    async def test_stego_tab_extract_text(self):
        # Hide text first
        from shared.stego_lab import StegoManager
        manager = StegoManager()
        manager.hide_text(self.input_img, "Secret Message", self.output_img)

        app = DummyStegoApp()

        async with app.run_test() as pilot:
            tab = app.query_one(StegoLabTab)

            # Set up mock notifications
            tab.notify = MagicMock()

            # Fill input for extraction
            extract_img_widget = tab.query_one("#stego-extract-img")
            extract_img_widget.value = self.output_img

            # Click Extract
            btn = tab.query_one("#btn-stego-extract")
            btn.press()
            await pilot.pause(0.1)

            # Check notification
            tab.notify.assert_called_with("Text extracted successfully.", severity="information")

            # Check text in output area
            output_text_widget = tab.query_one("#stego-output-text")
            self.assertEqual(output_text_widget.text, "Secret Message")
