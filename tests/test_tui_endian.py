import pytest
from textual.app import App
from shared.tui_endian import EndianLabTab

class EndianTestApp(App):
    def compose(self):
        yield EndianLabTab()

@pytest.mark.asyncio
async def test_endian_tui():
    app = EndianTestApp()
    async with app.run_test() as pilot:
        # Default mode is Hex String Swap

        # Test Hex
        await pilot.click("#input-hex")
        await pilot.press("0", "x", "A", "A", "B", "B")
        await pilot.click("#btn-swap-hex")

        result_hex = app.query_one("#result-hex").renderable
        # "Result: [bold green]0xBBAA[/bold green]"
        assert "0xBBAA" in str(result_hex)

        # Switch to Int
        await pilot.click("#radio-int")
        await pilot.pause()

        await pilot.click("#input-int")
        await pilot.press("0", "x", "1", "2", "3", "4", "5", "6", "7", "8")

        await pilot.click("#btn-swap-int")
        result_int = app.query_one("#result-int").renderable

        assert "0x78563412" in str(result_int)
