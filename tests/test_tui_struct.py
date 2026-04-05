import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from textual.app import App, ComposeResult
from shared.tui_struct import StructLabTab

class TestApp(App):
    def compose(self) -> ComposeResult:
        yield StructLabTab(Path("."))

class TestStructLabTab(unittest.IsolatedAsyncioTestCase):
    async def test_calc_size(self):
        app = TestApp()
        async with app.run_test() as pilot:
            tab = app.query_one(StructLabTab)

            # Mock manager
            tab.manager.calc_size = MagicMock(return_value=8)

            # Enter format
            app.query_one("#struct-calc-fmt").press()
        await pilot.pause()
            await pilot.press("i", "i")

            # Click Calculate
            app.query_one("#btn-struct-calc").press()
        await pilot.pause()

            # Check result
            lbl = app.query_one("#struct-calc-result")
            assert "8 bytes" in str(lbl.renderable)
            tab.manager.calc_size.assert_called_with("ii")

    async def test_hex_dump(self):
        app = TestApp()
        async with app.run_test() as pilot:
            tab = app.query_one(StructLabTab)

            # Mock manager
            tab.manager.get_hex_dump = MagicMock(return_value=[
                {"offset": "0000", "hex": "00 01", "ascii": ".."}
            ])

            # Switch to Hex Dump tab
            tabs = app.query_one("TabbedContent")
            tabs.active = "tab-struct-hex"
            await pilot.pause()

            # Enter path
            app.query_one("#struct-hex-path").press()
        await pilot.pause()
            await pilot.press("t", "e", "s", "t", ".", "b", "i", "n")

            # Click Dump
            app.query_one("#btn-struct-hex").press()
        await pilot.pause()

            # Check table
            table = app.query_one("#struct-hex-table")
            assert table.row_count == 1
            tab.manager.get_hex_dump.assert_called()

    async def test_pack(self):
        app = TestApp()
        async with app.run_test() as pilot:
            tab = app.query_one(StructLabTab)

            tab.manager.pack_data = MagicMock(return_value=10)

            # Switch to Pack tab
            tabs = app.query_one("TabbedContent")
            tabs.active = "tab-struct-pack"
            await pilot.pause()

            # Fill inputs
            app.query_one("#struct-pack-fmt").press()
        await pilot.pause()
            await pilot.press("i")

            app.query_one("#struct-pack-values").press()
        await pilot.pause()
            await pilot.press("1")

            app.query_one("#struct-pack-out").press()
        await pilot.pause()
            await pilot.press("o", "u", "t")

            # Click Pack
            app.query_one("#btn-struct-pack").press()
        await pilot.pause()

            # Check result
            lbl = app.query_one("#struct-pack-result")
            assert "Packed 10 bytes" in str(lbl.renderable)
            tab.manager.pack_data.assert_called()

if __name__ == "__main__":
    unittest.main()
