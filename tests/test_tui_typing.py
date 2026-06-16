import unittest
from pathlib import Path
from textual.app import App, ComposeResult
from shared.tui_typing import TypingLabTab

class TypingLabTestApp(App):
    def compose(self) -> ComposeResult:
        yield TypingLabTab(Path("."))

class TestTypingLabTab(unittest.IsolatedAsyncioTestCase):
    async def test_mount(self):
        app = TypingLabTestApp()
        async with app.run_test() as pilot:
            # Check if widgets exist
            tab = pilot.app.query_one(TypingLabTab)
            self.assertIsNotNone(tab)
            self.assertIsNotNone(pilot.app.query_one("#typing-select"))
            self.assertIsNotNone(pilot.app.query_one("#typing-input"))
            self.assertIsNotNone(pilot.app.query_one("#btn-typing-start"))

    async def test_start_session(self):
        app = TypingLabTestApp()
        async with app.run_test() as pilot:
            # Select snippet (simulation)
            # Textual Select is hard to drive programmatically in tests without specialized knowledge
            # But we can call methods directly on the widget

            tab = pilot.app.query_one(TypingLabTab)

            # Simulate snippet selection
            tab.target_text = "print('Hello')"
            tab.query_one("#btn-typing-start").disabled = False

            # Click start
            pilot.app.query_one("#btn-typing-start").press()
            await pilot.pause()

            self.assertTrue(tab.session_running)
            self.assertFalse(tab.query_one("#typing-input").disabled)

if __name__ == '__main__':
    unittest.main()
