import pytest
from typing import Any
from textual.app import App, ComposeResult
from textual.widgets import TextArea, Button
from shared.tui_binary import BinaryLabTab


class BinaryLabApp(App[Any]):
    def compose(self) -> ComposeResult:
        yield BinaryLabTab()


@pytest.mark.asyncio
async def test_binary_tab_encode():
    app = BinaryLabApp()
    async with app.run_test():
        tab = app.query_one(BinaryLabTab)
        input_area = app.query_one("#binary-input", TextArea)
        input_area.text = "Hello"
        encode_btn = app.query_one("#btn-binary-encode", Button)
        await tab.on_button_pressed(Button.Pressed(encode_btn))

        output_area = app.query_one("#binary-output", TextArea)
        assert output_area.text == "01001000 01100101 01101100 01101100 01101111"


@pytest.mark.asyncio
async def test_binary_tab_decode():
    app = BinaryLabApp()
    async with app.run_test():
        tab = app.query_one(BinaryLabTab)
        input_area = app.query_one("#binary-input", TextArea)
        input_area.text = "01001000 01100101 01101100 01101100 01101111"
        decode_btn = app.query_one("#btn-binary-decode", Button)
        await tab.on_button_pressed(Button.Pressed(decode_btn))

        output_area = app.query_one("#binary-output", TextArea)
        assert output_area.text == "Hello"


@pytest.mark.asyncio
async def test_binary_tab_swap():
    app = BinaryLabApp()
    async with app.run_test():
        tab = app.query_one(BinaryLabTab)
        input_area = app.query_one("#binary-input", TextArea)
        output_area = app.query_one("#binary-output", TextArea)

        input_area.text = "hello"
        output_area.text = "world"

        swap_btn = app.query_one("#btn-binary-swap", Button)
        await tab.on_button_pressed(Button.Pressed(swap_btn))

        assert input_area.text == "world"
        assert output_area.text == "hello"


@pytest.mark.asyncio
async def test_binary_tab_clear():
    app = BinaryLabApp()
    async with app.run_test():
        tab = app.query_one(BinaryLabTab)
        input_area = app.query_one("#binary-input", TextArea)
        output_area = app.query_one("#binary-output", TextArea)

        input_area.text = "hello"
        output_area.text = "world"

        clear_btn = app.query_one("#btn-binary-clear", Button)
        await tab.on_button_pressed(Button.Pressed(clear_btn))

        assert input_area.text == ""
        assert output_area.text == ""
