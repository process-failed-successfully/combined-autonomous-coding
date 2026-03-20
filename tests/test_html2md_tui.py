import unittest
from textual.app import App, ComposeResult
from typing import Any
from textual.widgets import TextArea
from shared.tui_html2md import Html2MdTab


class DummyApp(App[Any]):
    def compose(self) -> ComposeResult:
        yield Html2MdTab()


class TestHtml2MdTui(unittest.IsolatedAsyncioTestCase):
    async def test_tui_html2md_convert(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            # Set input
            app.query_one("#input-html", TextArea).text = "<p>Hello <b>World</b>!</p>"
            # Output is empty initially
            app.query_one("#output-md", TextArea).text = ""

            await pilot.click("#btn-convert")

            assert "Hello **World**!" in app.query_one("#output-md", TextArea).text

    async def test_tui_html2md_clear(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            app.query_one("#input-html", TextArea).text = "<p>Hello</p>"
            app.query_one("#output-md", TextArea).text = "Hello"

            await pilot.click("#btn-clear")

            assert app.query_one("#input-html", TextArea).text == ""
            assert app.query_one("#output-md", TextArea).text == ""
