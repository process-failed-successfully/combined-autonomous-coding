import pytest
from typing import Any
from textual.app import App, ComposeResult
from textual.widgets import TextArea, Checkbox, Button
from shared.tui_base32 import Base32LabTab


class Base32LabApp(App[Any]):
    def compose(self) -> ComposeResult:
        yield Base32LabTab()


@pytest.mark.asyncio
async def test_base32_tab_encode():
    app = Base32LabApp()
    async with app.run_test():
        tab = app.query_one(Base32LabTab)
        input_area = app.query_one("#b32-input", TextArea)
        input_area.text = "hello world"
        encode_btn = app.query_one("#btn-b32-encode", Button)
        await tab.on_button_pressed(Button.Pressed(encode_btn))

        output_area = app.query_one("#b32-output", TextArea)
        assert output_area.text == "NBSWY3DPEB3W64TMMQ======"


@pytest.mark.asyncio
async def test_base32_tab_decode():
    app = Base32LabApp()
    async with app.run_test():
        tab = app.query_one(Base32LabTab)
        input_area = app.query_one("#b32-input", TextArea)
        input_area.text = "NBSWY3DPEB3W64TMMQ======"
        decode_btn = app.query_one("#btn-b32-decode", Button)
        await tab.on_button_pressed(Button.Pressed(decode_btn))

        output_area = app.query_one("#b32-output", TextArea)
        assert output_area.text == "hello world"


@pytest.mark.asyncio
async def test_base32_tab_encode_hex():
    app = Base32LabApp()
    async with app.run_test():
        tab = app.query_one(Base32LabTab)
        hex_cb = app.query_one("#cb-b32-hex", Checkbox)
        hex_cb.value = True

        input_area = app.query_one("#b32-input", TextArea)
        input_area.text = "hello world"

        encode_btn = app.query_one("#btn-b32-encode", Button)
        await tab.on_button_pressed(Button.Pressed(encode_btn))

        output_area = app.query_one("#b32-output", TextArea)
        assert output_area.text == "D1IMOR3F41RMUSJCCG======"


@pytest.mark.asyncio
async def test_base32_tab_decode_hex():
    app = Base32LabApp()
    async with app.run_test():
        tab = app.query_one(Base32LabTab)
        hex_cb = app.query_one("#cb-b32-hex", Checkbox)
        hex_cb.value = True

        input_area = app.query_one("#b32-input", TextArea)
        input_area.text = "D1IMOR3F41RMUSJCCG======"

        decode_btn = app.query_one("#btn-b32-decode", Button)
        await tab.on_button_pressed(Button.Pressed(decode_btn))

        output_area = app.query_one("#b32-output", TextArea)
        assert output_area.text == "hello world"


@pytest.mark.asyncio
async def test_base32_tab_swap():
    app = Base32LabApp()
    async with app.run_test():
        tab = app.query_one(Base32LabTab)
        input_area = app.query_one("#b32-input", TextArea)
        output_area = app.query_one("#b32-output", TextArea)

        input_area.text = "hello"
        output_area.text = "world"

        swap_btn = app.query_one("#btn-b32-swap", Button)
        await tab.on_button_pressed(Button.Pressed(swap_btn))

        assert input_area.text == "world"
        assert output_area.text == "hello"


@pytest.mark.asyncio
async def test_base32_tab_clear():
    app = Base32LabApp()
    async with app.run_test():
        tab = app.query_one(Base32LabTab)
        input_area = app.query_one("#b32-input", TextArea)
        output_area = app.query_one("#b32-output", TextArea)

        input_area.text = "hello"
        output_area.text = "world"

        clear_btn = app.query_one("#btn-b32-clear", Button)
        await tab.on_button_pressed(Button.Pressed(clear_btn))

        assert input_area.text == ""
        assert output_area.text == ""
