import unittest
from typing import Any
from textual.app import App
from textual.widgets import Select, TextArea

from shared.tui_octal import OctalTab

class DummyApp(App[Any]):
    def compose(self):
        yield OctalTab()

class TestOctalTui(unittest.IsolatedAsyncioTestCase):

    async def test_encode_mode(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            input_area = app.query_one("#input-octal-text", TextArea)
            output_area = app.query_one("#output-octal-text", TextArea)

            input_area.text = "hello"
            await pilot.pause()

            self.assertEqual(output_area.text, "150 145 154 154 157")

    async def test_decode_mode(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            mode_select = app.query_one("#select-octal-mode", Select)
            mode_select.value = "decode"
            await pilot.pause()

            input_area = app.query_one("#input-octal-text", TextArea)
            output_area = app.query_one("#output-octal-text", TextArea)

            input_area.text = "150 145 154 154 157"
            await pilot.pause()

            self.assertEqual(output_area.text, "hello")

    async def test_decode_invalid(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            mode_select = app.query_one("#select-octal-mode", Select)
            mode_select.value = "decode"
            await pilot.pause()

            input_area = app.query_one("#input-octal-text", TextArea)
            output_area = app.query_one("#output-octal-text", TextArea)

            input_area.text = "150 xyz"
            await pilot.pause()

            self.assertEqual(output_area.text, "Error: Invalid octal string.")

    async def test_empty_input(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            input_area = app.query_one("#input-octal-text", TextArea)
            output_area = app.query_one("#output-octal-text", TextArea)

            input_area.text = ""
            await pilot.pause()

            self.assertEqual(output_area.text, "")

    async def test_blank_mode(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            mode_select = app.query_one("#select-octal-mode", Select)
            mode_select.clear()
            await pilot.pause()

            input_area = app.query_one("#input-octal-text", TextArea)
            output_area = app.query_one("#output-octal-text", TextArea)

            input_area.text = "hello"
            await pilot.pause()

            self.assertEqual(output_area.text, "")

if __name__ == '__main__':
    unittest.main()
