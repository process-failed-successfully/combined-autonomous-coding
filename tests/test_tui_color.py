import unittest
from textual.app import App, ComposeResult
from shared.tui_color import ColorLabTab
from textual.widgets import RichLog, Input, TabbedContent


class ColorLabApp(App[None]):
    def compose(self) -> ComposeResult:
        yield ColorLabTab()


class TestColorLabTab(unittest.IsolatedAsyncioTestCase):
    async def test_contrast_check(self):
        app = ColorLabApp()
        async with app.run_test() as pilot:
            # Inputs have default values #FFFFFF and #000000

            # Trigger check
            await pilot.click("#btn-cl-contrast")

            # Check results
            log = app.query_one("#cl-contrast-result", RichLog)
            # RichLog lines are Strip objects or Text objects
            text_content = "\n".join([str(line) for line in log.lines])

            self.assertIn("Contrast Ratio", text_content)
            self.assertIn("21.00:1", text_content)  # Black on White is max contrast
            self.assertIn("AAA (Pass)", text_content)

    async def test_convert(self):
        app = ColorLabApp()
        async with app.run_test() as pilot:
            # Activate Converter Tab
            tabbed = app.query_one("TabbedContent", TabbedContent)
            tabbed.active = "cl-tab-converter"
            await pilot.pause()  # Wait for tab switch animation/render

            # Set input
            app.query_one("#cl-convert-color", Input).value = "#ff0000"

            # Click convert
            await pilot.click("#btn-cl-convert")

            log = app.query_one("#cl-convert-result", RichLog)
            text_content = "\n".join([str(line) for line in log.lines])

            self.assertIn("(255, 0, 0)", text_content)
            self.assertIn("hsl(0.0, 100.0%, 50.0%)", text_content)

    async def test_invalid_color(self):
        app = ColorLabApp()
        async with app.run_test() as pilot:
            app.query_one("#cl-contrast-fg", Input).value = "invalid"
            await pilot.click("#btn-cl-contrast")

            log = app.query_one("#cl-contrast-result", RichLog)
            text_content = "\n".join([str(line) for line in log.lines])

            self.assertIn("Error", text_content)
