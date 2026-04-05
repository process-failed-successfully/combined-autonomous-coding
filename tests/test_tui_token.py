import unittest
from unittest.mock import MagicMock
from textual.app import App
from shared.tui_token import TokenLabTab


class MockApp(App):
    def compose(self):
        yield TokenLabTab()


class TestTokenLabTab(unittest.IsolatedAsyncioTestCase):
    async def test_tab_renders(self):
        app = MockApp()
        async with app.run_test():
            tab = app.query_one(TokenLabTab)
            self.assertIsNotNone(tab)
            # Find inputs
            text_input = app.query_one("#token-input-text")
            self.assertIsNotNone(text_input)
            token_input = app.query_one("#token-input-tokens")
            self.assertIsNotNone(token_input)

            # Find buttons
            count_btn = app.query_one("#btn-count")
            self.assertIsNotNone(count_btn)
            decode_btn = app.query_one("#btn-decode")
            self.assertIsNotNone(decode_btn)

    async def test_button_press_no_input(self):
        app = MockApp()
        async with app.run_test() as pilot:
            tab = app.query_one(TokenLabTab)
            tab.notify = MagicMock()

            app.query_one("#btn-count").press()
        await pilot.pause()
            tab.notify.assert_called_with("Please enter text to encode.", severity="error")

            app.query_one("#btn-decode").press()
        await pilot.pause()
            tab.notify.assert_called_with("Please enter tokens to decode.", severity="error")


if __name__ == '__main__':
    unittest.main()
