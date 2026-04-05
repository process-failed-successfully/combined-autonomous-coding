import unittest
from unittest.mock import MagicMock, patch
from shared.tui_md2html import Md2HtmlTab
from textual.widgets import TextArea, Button
from textual.app import App

class DummyApp(App):
    def compose(self):
        yield Md2HtmlTab()

class TestTuiMd2Html(unittest.IsolatedAsyncioTestCase):
    async def test_md2html_tab_render(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            # Check widgets exist
            input_md = app.query_one("#input-md", TextArea)
            output_html = app.query_one("#output-html", TextArea)
            self.assertIsNotNone(input_md)
            self.assertIsNotNone(output_html)

            # Test convert action
            input_md.text = "# Hello"
            pilot.app.query_one("#btn-convert").press()
            await pilot.pause()
            self.assertIn("<h1>Hello</h1>", output_html.text)

            # Test clear action
            pilot.app.query_one("#btn-clear").press()
            await pilot.pause()
            self.assertEqual(input_md.text, "")
            self.assertEqual(output_html.text, "")

if __name__ == "__main__":
    unittest.main()
