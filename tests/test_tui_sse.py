import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from textual.app import App, ComposeResult
import asyncio

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from shared.tui_sse import SseLabTab

class TestApp(App):
    def compose(self) -> ComposeResult:
        yield SseLabTab()

class TestTuiSse(unittest.IsolatedAsyncioTestCase):
    async def test_ui_elements(self):
        app = TestApp()
        async with app.run_test() as pilot:
            self.assertIsNotNone(app.query_one("#sse-url"))
            self.assertIsNotNone(app.query_one("#btn-sse-connect"))
            self.assertIsNotNone(app.query_one("#btn-sse-disconnect"))

if __name__ == "__main__":
    unittest.main()
