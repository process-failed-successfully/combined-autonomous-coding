import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from textual.app import App, ComposeResult
from shared.tui_sock import SockLabTab

class SockLabApp(App):
    def compose(self) -> ComposeResult:
        yield SockLabTab()

class TestSockLabTab(unittest.IsolatedAsyncioTestCase):
    async def test_ui_mount(self):
        app = SockLabApp()
        async with app.run_test(size=(120, 40)) as pilot:
            # Check widgets exist
            self.assertIsNotNone(pilot.app.query_one("#sock-mode"))
            self.assertIsNotNone(pilot.app.query_one("#sock-host"))
            self.assertIsNotNone(pilot.app.query_one("#btn-sock-connect"))

    async def test_connect_button(self):
        with patch("shared.tui_sock.SockLabManager") as MockManagerClass:
            # Setup the mock instance
            mock_instance = MockManagerClass.return_value
            mock_instance.start_client = AsyncMock()
            mock_instance.start_server = AsyncMock()

            app = SockLabApp()
            async with app.run_test(size=(120, 40)) as pilot:
                # Click Connect
                btn = pilot.app.query_one("#btn-sock-connect")
                btn.press()

                # Wait for event processing
                await pilot.pause()

                # Since connect() re-instantiates SockLabManager, the mock class is called again.
                # By default, Mock return_value returns the same instance every time.

                mock_instance.start_client.assert_called()

                # Check button state
                self.assertTrue(pilot.app.query_one("#btn-sock-connect").disabled)

if __name__ == "__main__":
    unittest.main()
