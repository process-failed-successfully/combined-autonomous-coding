import unittest
import pytest
import shutil
from textual.app import App, ComposeResult
from textual.widgets import TextArea, RichLog, Button
from shared.tui_js import JsLabTab

HAS_NODE = shutil.which("node") is not None

class DummyApp(App[None]):
    def compose(self) -> ComposeResult:
        yield JsLabTab(id="js-lab")

@pytest.mark.asyncio
class TestTuiJsLab(unittest.IsolatedAsyncioTestCase):
    async def test_js_lab_tui_render(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            tab = app.query_one(JsLabTab)
            self.assertIsNotNone(tab)

            # Check that UI components exist
            self.assertIsNotNone(app.query_one("#js-input", TextArea))
            self.assertIsNotNone(app.query_one("#btn-js-run", Button))
            self.assertIsNotNone(app.query_one("#btn-js-minify", Button))
            self.assertIsNotNone(app.query_one("#js-output", RichLog))

    @unittest.skipIf(not HAS_NODE, "Node.js not installed")
    async def test_js_lab_run_action(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            # Set input
            input_area = app.query_one("#js-input", TextArea)
            input_area.text = "console.log('TUI JS Test');"

            # Click run
            run_btn = app.query_one("#btn-js-run", Button)
            run_btn.press()

            # It's an async UI event, pilot.click handles some delay but we might need a tick
            await pilot.pause()

            # Output should contain "TUI JS Test"
            output_log = app.query_one("#js-output", RichLog)
            output_text = "\n".join([line.text.plain if hasattr(line.text, 'plain') else str(line.text) for line in output_log.lines])
            self.assertIn("TUI JS Test", output_text)

    async def test_js_lab_minify_action(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            # Set input
            input_area = app.query_one("#js-input", TextArea)
            input_area.text = "function a() { \n // comment \n return 1; \n }"

            # Click minify
            minify_btn = app.query_one("#btn-js-minify", Button)
            minify_btn.press()

            await pilot.pause()

            # Output should contain minified text
            output_log = app.query_one("#js-output", RichLog)
            output_text = "\n".join([line.text.plain if hasattr(line.text, 'plain') else str(line.text) for line in output_log.lines])
            self.assertIn("function a() { return 1; }", output_text)
