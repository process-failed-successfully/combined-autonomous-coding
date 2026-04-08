import unittest
from typing import Any
from textual.app import App, ComposeResult
from textual.widgets import TextArea

from shared.tui_html2md import Html2MdTab

class DummyApp(App[Any]):
    def compose(self) -> ComposeResult:
        yield Html2MdTab()

class TestHtml2MdTui(unittest.IsolatedAsyncioTestCase):
    async def test_tui_html2md_convert(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            tab = app.query_one(Html2MdTab)

            input_area = tab.query_one("#input-html", TextArea)
            output_area = tab.query_one("#output-md", TextArea)

            input_area.text = "<p>Hello <b>World</b>!</p>"

            await pilot.click("#btn-convert")

            self.assertIn("Hello **World**!", output_area.text)

    async def test_tui_html2md_clear(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            tab = app.query_one(Html2MdTab)

            input_area = tab.query_one("#input-html", TextArea)
            output_area = tab.query_one("#output-md", TextArea)

            input_area.text = "<p>Hello</p>"
            output_area.text = "Hello"

            await pilot.click("#btn-clear")

            self.assertEqual(input_area.text, "")
            self.assertEqual(output_area.text, "")
