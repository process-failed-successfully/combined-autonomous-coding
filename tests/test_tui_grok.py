from typing import Any
import unittest
import asyncio
from unittest.mock import patch, MagicMock
from textual.widgets import Input, Markdown
from shared.tui_grok import GrokLabTab
from textual.app import App
from textual.widgets import TabbedContent


class DummyApp(App[Any]):
    def compose(self):
        with TabbedContent():
            yield GrokLabTab()


class TestGrokTui(unittest.IsolatedAsyncioTestCase):
    async def test_grok_lab_tab(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            # Check components exist
            self.assertIsNotNone(app.query_one("#grok-pattern"))
            self.assertIsNotNone(app.query_one("#grok-text"))
            self.assertIsNotNone(app.query_one("#grok-parse-btn"))

            with patch.object(Markdown, 'update', new_callable=MagicMock) as mock_markdown_update:
                # Interact
                app.query_one("#grok-pattern", Input).value = "%{IPV4:ip}"
                app.query_one("#grok-text", Input).value = "1.2.3.4"
                await pilot.click("#grok-parse-btn")

                await asyncio.sleep(0.1)  # Wait for update

                mock_markdown_update.assert_called()
                called_text = mock_markdown_update.call_args[0][0]
                self.assertIn("1.2.3.4", called_text)


if __name__ == '__main__':
    unittest.main()
