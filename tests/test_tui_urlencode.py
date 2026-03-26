import unittest
from typing import Any
from textual.app import App
from textual.widgets import TextArea, Button
from shared.tui_urlencode import UrlEncodeLabTab
import urllib.parse


class DummyApp(App[Any]):
    def compose(self):
        yield UrlEncodeLabTab()


class TestUrlEncodeLabTab(unittest.IsolatedAsyncioTestCase):
    async def test_encode_success(self) -> None:
        app = DummyApp()
        async with app.run_test(size=(200, 200)) as pilot:
            input_area = app.query_one("#urlencode-input", TextArea)
            input_area.text = "hello world/&?"

            btn = app.query_one("#btn-urlencode-encode", Button)
            btn.press()
            await pilot.pause()

            output_area = app.query_one("#urlencode-output", TextArea)
            self.assertEqual(output_area.text, "hello%20world/%26%3F")

    async def test_decode_success(self) -> None:
        app = DummyApp()
        async with app.run_test(size=(200, 200)) as pilot:
            input_area = app.query_one("#urlencode-input", TextArea)
            input_area.text = "hello%20world%2F%26%3F"

            btn = app.query_one("#btn-urlencode-decode", Button)
            btn.press()
            await pilot.pause()

            output_area = app.query_one("#urlencode-output", TextArea)
            self.assertEqual(output_area.text, "hello world/&?")

    async def test_empty_input(self) -> None:
        app = DummyApp()
        async with app.run_test(size=(200, 200)) as pilot:
            input_area = app.query_one("#urlencode-input", TextArea)
            input_area.text = ""

            btn = app.query_one("#btn-urlencode-encode", Button)
            btn.press()
            await pilot.pause()

            output_area = app.query_one("#urlencode-output", TextArea)
            self.assertEqual(output_area.text, "")

    async def test_swap_content(self) -> None:
        app = DummyApp()
        async with app.run_test(size=(200, 200)) as pilot:
            input_area = app.query_one("#urlencode-input", TextArea)
            output_area = app.query_one("#urlencode-output", TextArea)
            input_area.text = "input_text"
            output_area.text = "output_text"

            btn = app.query_one("#btn-urlencode-swap", Button)
            btn.press()
            await pilot.pause()

            self.assertEqual(input_area.text, "output_text")
            self.assertEqual(output_area.text, "input_text")

    async def test_clear_content(self) -> None:
        app = DummyApp()
        async with app.run_test(size=(200, 200)) as pilot:
            input_area = app.query_one("#urlencode-input", TextArea)
            output_area = app.query_one("#urlencode-output", TextArea)
            input_area.text = "input_text"
            output_area.text = "output_text"

            btn = app.query_one("#btn-urlencode-clear", Button)
            btn.press()
            await pilot.pause()

            self.assertEqual(input_area.text, "")
            self.assertEqual(output_area.text, "")

    async def test_exception_handling(self) -> None:
        app = DummyApp()
        async with app.run_test(size=(200, 200)) as pilot:
            input_area = app.query_one("#urlencode-input", TextArea)
            input_area.text = "hello"

            # Monkeypatch urllib.parse.quote to raise an Exception
            original_quote = urllib.parse.quote

            def mock_quote(*args, **kwargs):
                raise Exception("Mock error")
            urllib.parse.quote = mock_quote

            try:
                btn = app.query_one("#btn-urlencode-encode", Button)
                btn.press()
                await pilot.pause()
                output_area = app.query_one("#urlencode-output", TextArea)
                self.assertEqual(output_area.text, "Error: Mock error")
            finally:
                urllib.parse.quote = original_quote


if __name__ == "__main__":
    unittest.main()
