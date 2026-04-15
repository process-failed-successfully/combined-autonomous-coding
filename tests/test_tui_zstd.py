import unittest
import base64
import pytest
from textual.app import App
from textual.widgets import TextArea, Checkbox, Select

from shared.tui_zstd import ZstdLabTab

class ZstdTestApp(App):
    def compose(self):
        yield ZstdLabTab()

class TestTuiZstd(unittest.IsolatedAsyncioTestCase):
    @pytest.mark.asyncio
    async def test_zstd_tab_compression_hex(self):
        app = ZstdTestApp()
        async with app.run_test() as pilot:
            tab = app.query_one(ZstdLabTab)

            # Switch base64 to False
            cb = tab.query_one("#zstd-base64", Checkbox)
            cb.value = False
            await pilot.pause()

            # Enter text to compress
            input_area = tab.query_one("#zstd-input-text", TextArea)
            input_area.focus()
            input_area.text = "Hello Zstandard"
            await pilot.pause()

            # Check compressed output
            compressed_area = tab.query_one("#zstd-compressed-text", TextArea)
            out_hex = compressed_area.text.strip()
            self.assertTrue(len(out_hex) > 0)
            self.assertTrue(all(c in "0123456789abcdefABCDEF" for c in out_hex))

    @pytest.mark.asyncio
    async def test_zstd_tab_compression_base64(self):
        app = ZstdTestApp()
        async with app.run_test() as pilot:
            tab = app.query_one(ZstdLabTab)

            # Base64 is default True
            cb = tab.query_one("#zstd-base64", Checkbox)
            self.assertTrue(cb.value)

            # Enter text to compress
            input_area = tab.query_one("#zstd-input-text", TextArea)
            input_area.focus()
            input_area.text = "Hello Zstandard"
            await pilot.pause()

            # Check compressed output
            compressed_area = tab.query_one("#zstd-compressed-text", TextArea)
            out_b64 = compressed_area.text.strip()
            self.assertTrue(len(out_b64) > 0)

            # Verify valid base64
            decoded = base64.b64decode(out_b64)
            self.assertTrue(len(decoded) > 0)

if __name__ == '__main__':
    unittest.main()
