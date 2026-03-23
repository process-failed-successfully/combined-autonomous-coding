import unittest
from textual.app import App
from shared.tui_brotli import BrotliLabTab
from textual.widgets import TextArea, Select, Checkbox

class DummyApp(App):
    def compose(self):
        yield BrotliLabTab()

class TestTuiBrotli(unittest.IsolatedAsyncioTestCase):
    async def test_brotli_tab_compression_hex(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            tab = app.query_one(BrotliLabTab)

            # Uncheck base64 to use hex
            cb = tab.query_one("#brotli-base64", Checkbox)
            cb.value = False

            # Input text
            input_area = tab.query_one("#brotli-input-text", TextArea)
            input_area.text = "Hex compress me"

            # Select quality
            sel = tab.query_one("#brotli-quality", Select)
            sel.value = 11

            await pilot.click("#btn-compress")

            compressed_area = tab.query_one("#brotli-compressed-text", TextArea)
            self.assertTrue(len(compressed_area.text) > 0)
            self.assertNotEqual(compressed_area.text, "Hex compress me")

            # Verify decompression
            input_area.text = ""
            await pilot.click("#btn-decompress")
            self.assertEqual(input_area.text, "Hex compress me")

    async def test_brotli_tab_compression_base64(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            tab = app.query_one(BrotliLabTab)

            # Make sure base64 is checked
            cb = tab.query_one("#brotli-base64", Checkbox)
            cb.value = True

            # Input text
            input_area = tab.query_one("#brotli-input-text", TextArea)
            input_area.text = "Base64 compress me"

            await pilot.click("#btn-compress")

            compressed_area = tab.query_one("#brotli-compressed-text", TextArea)
            self.assertTrue(len(compressed_area.text) > 0)
            self.assertNotEqual(compressed_area.text, "Base64 compress me")

            # Verify decompression
            input_area.text = ""
            await pilot.click("#btn-decompress")
            self.assertEqual(input_area.text, "Base64 compress me")
