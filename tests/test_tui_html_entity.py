import unittest
from typing import Any
from textual.app import App, ComposeResult
from textual.widgets import TextArea, Static, Button
from shared.tui_html_entity import HtmlEntityTab

class DummyApp(App[Any]):
    def compose(self) -> ComposeResult:
        yield HtmlEntityTab()

class TestHtmlEntityTUI(unittest.IsolatedAsyncioTestCase):
    async def test_encode(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            # Type text to encode
            input_widget = app.query_one("#html-entity-input", TextArea)
            input_widget.text = "<script>alert('xss');</script>"

            # Click encode
            await pilot.click("#btn-html-entity-encode")

            # Verify output
            output_widget = app.query_one("#html-entity-output", TextArea)
            expected = "&lt;script&gt;alert(&#x27;xss&#x27;);&lt;/script&gt;"
            self.assertEqual(output_widget.text, expected)

            # Verify status
            status_widget = app.query_one("#html-entity-status", Static)
            self.assertIn("Successfully encoded", str(status_widget.render()))

    async def test_decode(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            # Type entities to decode
            input_widget = app.query_one("#html-entity-input", TextArea)
            input_widget.text = "AT&amp;T &lt;html&gt;"

            # Click decode
            await pilot.click("#btn-html-entity-decode")

            # Verify output
            output_widget = app.query_one("#html-entity-output", TextArea)
            expected = "AT&T <html>"
            self.assertEqual(output_widget.text, expected)

            # Verify status
            status_widget = app.query_one("#html-entity-status", Static)
            self.assertIn("Successfully decoded", str(status_widget.render()))

    async def test_empty_input(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            # Ensure input is empty
            input_widget = app.query_one("#html-entity-input", TextArea)
            input_widget.text = ""

            # Click encode
            await pilot.click("#btn-html-entity-encode")

            # Verify status
            status_widget = app.query_one("#html-entity-status", Static)
            self.assertIn("Please enter text", str(status_widget.render()))

            # Click decode
            await pilot.click("#btn-html-entity-decode")

            # Verify status
            status_widget = app.query_one("#html-entity-status", Static)
            self.assertIn("Please enter HTML entities", str(status_widget.render()))

    async def test_clear(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            # Put some text
            input_widget = app.query_one("#html-entity-input", TextArea)
            output_widget = app.query_one("#html-entity-output", TextArea)
            status_widget = app.query_one("#html-entity-status", Static)

            input_widget.text = "Test"
            output_widget.text = "Output"
            status_widget.update("Status")

            # Click clear
            await pilot.click("#btn-html-entity-clear")

            # Verify everything is cleared
            self.assertEqual(input_widget.text, "")
            self.assertEqual(output_widget.text, "")
            self.assertEqual(str(status_widget.render()), "")
