import pytest
from typing import Any
from textual.app import App, ComposeResult
from textual.widgets import TextArea
from shared.tui_braille import BrailleLabTab


class DummyBrailleApp(App[Any]):
    def compose(self) -> ComposeResult:
        yield BrailleLabTab()


@pytest.mark.asyncio
async def test_braille_tab():
    app = DummyBrailleApp()
    async with app.run_test() as pilot:
        await pilot.pause(0.1)

        text_input = app.query_one("#braille-text-input", TextArea)
        braille_output = app.query_one("#braille-output", TextArea)

        # Type text, see braille
        text_input.text = "hello"
        await pilot.pause(0.1)
        assert braille_output.text == "⠓⠑⠇⠇⠕"

        # Click clear
        await pilot.click("#braille-clear-btn")
        await pilot.pause(0.1)
        assert text_input.text == ""
        assert braille_output.text == ""

        # Type braille, see text
        braille_output.text = "⠺⠕⠗⠇⠙"
        await pilot.pause(0.1)
        assert text_input.text == "world"
