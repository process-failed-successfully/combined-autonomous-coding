import pytest
from shared.base100_lab import base100_encode, base100_decode

def test_base100_encode():
    assert base100_encode(b"hello") == "👨👥👬👬👯"

def test_base100_decode():
    assert base100_decode("👨👥👬👬👯") == b"hello"
import pytest
from textual.app import App
from shared.tui_base100 import Base100LabTab
from textual.widgets import Button
import asyncio

class DummyApp(App):
    def compose(self):
        yield Base100LabTab()

@pytest.mark.asyncio
async def test_base100_encode_tui():
    app = DummyApp()
    async with app.run_test() as pilot:
        # Get input
        input_area = app.query_one("#b100-input")
        input_area.text = "hello"

        # Click encode using press
        btn = app.query_one("#btn-b100-encode", Button)
        btn.press()
        await pilot.pause()

        # Check output
        output_area = app.query_one("#b100-output")
        assert output_area.text == "👨👥👬👬👯"

@pytest.mark.asyncio
async def test_base100_decode_tui():
    app = DummyApp()
    async with app.run_test() as pilot:
        # Get input
        input_area = app.query_one("#b100-input")
        input_area.text = "👨👥👬👬👯"

        # Click decode using press
        btn = app.query_one("#btn-b100-decode", Button)
        btn.press()
        await pilot.pause()

        # Check output
        output_area = app.query_one("#b100-output")
        assert output_area.text == "hello"

@pytest.mark.asyncio
async def test_base100_swap_tui():
    app = DummyApp()
    async with app.run_test() as pilot:
        app.query_one("#b100-input").text = "abc"
        app.query_one("#b100-output").text = "xyz"
        btn = app.query_one("#btn-b100-swap", Button)
        btn.press()
        await pilot.pause()

        assert app.query_one("#b100-input").text == "xyz"
        assert app.query_one("#b100-output").text == "abc"

@pytest.mark.asyncio
async def test_base100_clear_tui():
    app = DummyApp()
    async with app.run_test() as pilot:
        app.query_one("#b100-input").text = "abc"
        app.query_one("#b100-output").text = "xyz"
        btn = app.query_one("#btn-b100-clear", Button)
        btn.press()
        await pilot.pause()

        assert app.query_one("#b100-input").text == ""
        assert app.query_one("#b100-output").text == ""
