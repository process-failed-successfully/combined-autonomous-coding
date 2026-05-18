import pytest
from textual.app import App
from shared.tui_float import FloatLabTab
from pathlib import Path
from textual.widgets import Input, Button

class FloatLabTestApp(App):
    def compose(self):
        yield FloatLabTab(Path("."))

@pytest.mark.asyncio
async def test_float_lab_tui():
    app = FloatLabTestApp()
    async with app.run_test() as pilot:
        await pilot.pause()

        # Test encode
        input_float = app.query_one("#input-float", Input)
        input_float.value = "-12.5"

        app.query_one("#btn-float-convert", Button).press()
        await pilot.pause()

        out_value = app.query_one("#out-float-value", Input).value
        out_hex = app.query_one("#out-float-hex", Input).value
        assert out_value == "-12.5"
        assert out_hex == "c1480000"

        # Test decode
        await pilot.click("#rb-decode")
        input_float.value = "3fb999999999999a"
        await pilot.click("#rb-double")
        app.query_one("#btn-float-convert", Button).press()
        await pilot.pause()

        out_value2 = app.query_one("#out-float-value", Input).value
        out_hex2 = app.query_one("#out-float-hex", Input).value
        assert out_value2 == "0.1"
        assert out_hex2 == "3fb999999999999a"
