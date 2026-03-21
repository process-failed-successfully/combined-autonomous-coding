import unittest
from typing import Any
from textual.app import App, ComposeResult
from textual.widgets import TextArea, Button

from shared.tui_punycode import PunycodeLabTab


class DummyApp(App[Any]):
    def compose(self) -> ComposeResult:
        yield PunycodeLabTab()


class TestPunycodeLabTab(unittest.IsolatedAsyncioTestCase):

    async def test_punycode_tab_render(self):
        app = DummyApp()
        async with app.run_test():
            tab = app.query_one(PunycodeLabTab)
            self.assertIsNotNone(tab)
            input_area = app.query_one("#punycode-input", TextArea)
            output_area = app.query_one("#punycode-output", TextArea)
            self.assertIsNotNone(input_area)
            self.assertIsNotNone(output_area)

    async def test_punycode_input_encode(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            input_area = app.query_one("#punycode-input", TextArea)
            input_area.text = "münchen.de"
            btn = app.query_one("#btn-punycode-encode", Button)
            btn.press()
            await pilot.pause(0.1)
            output_area = app.query_one("#punycode-output", TextArea)
            self.assertEqual(output_area.text, "xn--mnchen-3ya.de")

    async def test_punycode_input_decode(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            input_area = app.query_one("#punycode-input", TextArea)
            input_area.text = "xn--mnchen-3ya.de"
            btn = app.query_one("#btn-punycode-decode", Button)
            btn.press()
            await pilot.pause(0.1)
            output_area = app.query_one("#punycode-output", TextArea)
            self.assertEqual(output_area.text, "münchen.de")
