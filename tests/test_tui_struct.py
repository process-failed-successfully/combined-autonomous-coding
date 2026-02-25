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
            await pilot.click("#struct-calc-fmt")
            await pilot.press("i", "i")

            # Click Calculate
            await pilot.click("#btn-struct-calc")

            # Check result
            lbl = app.query_one("#struct-calc-result")
            assert "8 bytes" in str(lbl.render())
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
            await pilot.click("#struct-hex-path")
            await pilot.press("t", "e", "s", "t", ".", "b", "i", "n")

            # Click Dump
            await pilot.click("#btn-struct-hex")

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
            await pilot.click("#struct-pack-fmt")
            await pilot.press("i")

            await pilot.click("#struct-pack-values")
            await pilot.press("1")

            await pilot.click("#struct-pack-out")
            await pilot.press("o", "u", "t")

            # Click Pack
            await pilot.click("#btn-struct-pack")

            # Check result
            lbl = app.query_one("#struct-pack-result")
            assert "Packed 10 bytes" in str(lbl.render())
            tab.manager.pack_data.assert_called()

if __name__ == "__main__":
    unittest.main()
