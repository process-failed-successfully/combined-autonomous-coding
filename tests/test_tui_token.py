import unittest
from textual.app import App, ComposeResult
from textual.widgets import TextArea, Select, Button, RichLog

from shared.tui_token import TokenLabTab


class DummyApp(App):
    def compose(self) -> ComposeResult:
        yield TokenLabTab()


class TestTuiToken(unittest.IsolatedAsyncioTestCase):
    async def test_token_lab_mounts_and_counts(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            tab = app.query_one(TokenLabTab)
            self.assertIsNotNone(tab)

            # Set text
            text_input = tab.query_one("#token-text-input", TextArea)
            text_input.text = "Hello world from the token lab!"

            # Select model
            model_select = tab.query_one("#token-model-select", Select)
            model_select.value = "gpt-4o"

            # Click count button
            btn = tab.query_one("#btn-token-count", Button)
            btn.press()

            await pilot.pause()

            # Check output
            log = tab.query_one("#token-result-log", RichLog)
            content = "\n".join([line.text for line in log.lines])

            self.assertIn("Token Count (gpt-4o):", content)
            self.assertIn("Token IDs", content)

    async def test_token_lab_empty_text(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            tab = app.query_one(TokenLabTab)

            # Ensure text is empty
            text_input = tab.query_one("#token-text-input", TextArea)
            text_input.text = ""

            # Click count button
            btn = tab.query_one("#btn-token-count", Button)
            btn.press()

            await pilot.pause()

            # Since notify is used, we just check that log didn't change/get results
            log = tab.query_one("#token-result-log", RichLog)
            content = "\n".join([line.text for line in log.lines])
            self.assertEqual(content, "")
