import unittest
import asyncio
from textual.app import App, ComposeResult
from textual.widgets import TextArea, Button, Switch, Input

from shared.tui_html2jsx import Html2JsxLabTab

class DummyApp(App):
    def compose(self) -> ComposeResult:
        yield Html2JsxLabTab()

class TestHtml2JsxLabTui(unittest.IsolatedAsyncioTestCase):
    async def test_html2jsx_tab_render(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            # Check if all key elements are present
            self.assertIsNotNone(app.query_one("#html-input"))
            self.assertIsNotNone(app.query_one("#jsx-output"))
            self.assertIsNotNone(app.query_one("#btn-convert"))
            self.assertIsNotNone(app.query_one("#btn-clear"))
            self.assertIsNotNone(app.query_one("#switch-component"))
            self.assertIsNotNone(app.query_one("#input-component-name"))

    async def test_convert_html(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            # Type input HTML
            input_area = app.query_one("#html-input", TextArea)
            input_area.text = '<div class="test">content</div>'

            # Click convert
            app.query_one("#btn-convert").press()
        await pilot.pause()
            await asyncio.sleep(0.05)

            # Check output
            output_area = app.query_one("#jsx-output", TextArea)
            self.assertEqual(output_area.text, '<div className="test">content</div>')

    async def test_convert_html_with_component(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            # Setup input and options
            app.query_one("#html-input", TextArea).text = '<img src="test.png">'
            app.query_one("#switch-component", Switch).value = True
            app.query_one("#input-component-name", Input).value = "TestComp"

            # Convert
            app.query_one("#btn-convert").press()
        await pilot.pause()
            await asyncio.sleep(0.05)

            # Verify output
            output_area = app.query_one("#jsx-output", TextArea)
            expected = "export default function TestComp() {\n  return (\n    <>\n      <img src=\"test.png\" />\n    </>\n  );\n}"
            self.assertEqual(output_area.text, expected)

    async def test_clear_button(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            app.query_one("#html-input", TextArea).text = "<div>test</div>"
            app.query_one("#jsx-output", TextArea).text = "<div>test</div>"

            app.query_one("#btn-clear").press()
        await pilot.pause()
            await asyncio.sleep(0.05)

            self.assertEqual(app.query_one("#html-input", TextArea).text, "")
            self.assertEqual(app.query_one("#jsx-output", TextArea).text, "")

if __name__ == '__main__':
    unittest.main()
