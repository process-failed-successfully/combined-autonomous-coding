import pytest
from textual.app import App
from shared.tui_enc import EncLabTab
from textual.widgets import TextArea, Select, Switch

class DummyApp(App):
    def compose(self):
        yield EncLabTab()

@pytest.mark.asyncio
async def test_enc_lab_tab_base64_encode():
    app = DummyApp()
    async with app.run_test() as pilot:
        # Give it a moment to mount
        await pilot.pause()

        # By default, algorithm should be base64, encode mode
        algo_select = app.query_one("#enc-algorithm-select", Select)
        assert algo_select.value == "base64"

        mode_switch = app.query_one("#enc-mode-switch", Switch)
        assert mode_switch.value is False  # Encode mode

        # Set input text
        input_area = app.query_one("#enc-input", TextArea)
        input_area.load_text("Hello World")
        await pilot.pause()

        # Check output
        output_area = app.query_one("#enc-output", TextArea)
        assert output_area.text == "SGVsbG8gV29ybGQ="

@pytest.mark.asyncio
async def test_enc_lab_tab_base64_decode():
    app = DummyApp()
    async with app.run_test() as pilot:
        await pilot.pause()

        mode_switch = app.query_one("#enc-mode-switch", Switch)
        mode_switch.value = True # Decode mode

        input_area = app.query_one("#enc-input", TextArea)
        input_area.load_text("SGVsbG8gV29ybGQ=")
        await pilot.pause()

        output_area = app.query_one("#enc-output", TextArea)
        assert output_area.text == "Hello World"

@pytest.mark.asyncio
async def test_enc_lab_tab_hex_encode():
    app = DummyApp()
    async with app.run_test() as pilot:
        await pilot.pause()

        algo_select = app.query_one("#enc-algorithm-select", Select)
        algo_select.value = "hex"

        input_area = app.query_one("#enc-input", TextArea)
        input_area.load_text("Hello")
        await pilot.pause()

        output_area = app.query_one("#enc-output", TextArea)
        assert output_area.text == "48656c6c6f"

@pytest.mark.asyncio
async def test_enc_lab_tab_hex_decode_invalid():
    app = DummyApp()
    async with app.run_test() as pilot:
        await pilot.pause()

        algo_select = app.query_one("#enc-algorithm-select", Select)
        algo_select.value = "hex"

        mode_switch = app.query_one("#enc-mode-switch", Switch)
        mode_switch.value = True # Decode mode

        input_area = app.query_one("#enc-input", TextArea)
        input_area.load_text("NotHex")
        await pilot.pause()

        output_area = app.query_one("#enc-output", TextArea)
        assert "Error:" in output_area.text
        assert "Invalid Hex string" in output_area.text

@pytest.mark.asyncio
async def test_enc_lab_tab_rot13():
    app = DummyApp()
    async with app.run_test() as pilot:
        await pilot.pause()

        algo_select = app.query_one("#enc-algorithm-select", Select)
        algo_select.value = "rot13"

        input_area = app.query_one("#enc-input", TextArea)
        input_area.load_text("Hello")
        await pilot.pause()

        output_area = app.query_one("#enc-output", TextArea)
        assert output_area.text == "Uryyb"
