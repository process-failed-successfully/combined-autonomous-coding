import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from textual.app import App, ComposeResult
from textual.widgets import Input

from shared.tui_http_server import HttpServerLabTab


class TestApp(App):
    CSS = """
    .stat-box {
        height: auto;
        border: solid green;
        margin: 1;
    }
    Horizontal {
        height: auto;
    }
    Input {
        height: 3;
    }
    Button {
        height: 3;
        width: 20;
    }
    """

    def __init__(self, tab):
        super().__init__()
        self.tab = tab

    def compose(self) -> ComposeResult:
        yield self.tab


class TestHttpServerLabTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tab = HttpServerLabTab(Path("/tmp"))
        self.tab.notify = MagicMock()
        self.app = TestApp(self.tab)

    async def test_mount(self):
        async with self.app.run_test(size=(200, 100)) as pilot:
            self.assertIsNotNone(pilot.app.query_one("#static-path"))

    async def test_start_static(self):
        self.tab.manager = AsyncMock()

        async with self.app.run_test(size=(200, 100)):
            # Simulate input
            self.tab.query_one("#static-path", Input).value = "/test/path"
            self.tab.query_one("#static-port", Input).value = "9000"

            # Call handler directly to avoid layout/click issues in headless test
            await self.tab.on_static_start()

            self.tab.manager.start_static.assert_called_with("/test/path", 9000)
            self.assertTrue(self.tab.query_one("#btn-static-start").disabled)

    async def test_start_echo(self):
        self.tab.manager = AsyncMock()

        async with self.app.run_test(size=(200, 100)):
            self.tab.query_one("#echo-port", Input).value = "9001"

            await self.tab.on_echo_start()

            self.tab.manager.start_echo.assert_called_with(9001)
            self.assertTrue(self.tab.query_one("#btn-echo-start").disabled)


if __name__ == '__main__':
    unittest.main()
