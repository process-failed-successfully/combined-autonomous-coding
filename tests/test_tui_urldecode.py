import pytest
pytest.importorskip("textual")

from textual.app import App, ComposeResult
from textual.widgets import TextArea, TabbedContent
from shared.tui_urldecode import UrlDecodeLabTab


class UrldecodeTestApp(App):
    def compose(self) -> ComposeResult:
        with TabbedContent():
            yield UrlDecodeLabTab()


@pytest.mark.asyncio
async def test_urldecode_lab_tab_decode():
    app = UrldecodeTestApp()
    async with app.run_test() as pilot:
        tab = app.query_one(UrlDecodeLabTab)

        input_area = app.query_one("#urldecode-input", TextArea)
        output_area = app.query_one("#urldecode-output", TextArea)

        # Set input text
        input_area.text = "hello%20world%21"

        # Click the Decode button
        tab.process()
        await pilot.pause(0.1)

        assert output_area.text == "hello world!"


@pytest.mark.asyncio
async def test_urldecode_lab_tab_swap():
    app = UrldecodeTestApp()
    async with app.run_test() as pilot:
        tab = app.query_one(UrlDecodeLabTab)

        input_area = app.query_one("#urldecode-input", TextArea)
        output_area = app.query_one("#urldecode-output", TextArea)

        # Initial state
        input_area.text = "foo"
        output_area.text = "bar"

        # Click the Swap button
        tab.swap_content()
        await pilot.pause(0.1)

        assert input_area.text == "bar"
        assert output_area.text == "foo"


@pytest.mark.asyncio
async def test_urldecode_lab_tab_clear():
    app = UrldecodeTestApp()
    async with app.run_test() as pilot:
        tab = app.query_one(UrlDecodeLabTab)

        input_area = app.query_one("#urldecode-input", TextArea)
        output_area = app.query_one("#urldecode-output", TextArea)

        input_area.text = "input text"
        output_area.text = "output text"

        # Click the Clear button
        tab.clear_content()
        await pilot.pause(0.1)

        assert input_area.text == ""
        assert output_area.text == ""


@pytest.mark.asyncio
async def test_urldecode_lab_tab_empty_input():
    app = UrldecodeTestApp()
    async with app.run_test() as pilot:
        tab = app.query_one(UrlDecodeLabTab)

        input_area = app.query_one("#urldecode-input", TextArea)
        output_area = app.query_one("#urldecode-output", TextArea)

        input_area.text = ""
        output_area.text = "should not change"

        # Click the Decode button
        tab.process()
        await pilot.pause(0.1)

        assert output_area.text == "should not change"
