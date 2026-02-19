import unittest
from unittest.mock import patch
from textual.app import App, ComposeResult
from textual.widgets import Button
from shared.tui_proxy import ProxyLabTab


class ProxyTestApp(App):
    def compose(self) -> ComposeResult:
        yield ProxyLabTab()


class TestTuiProxy(unittest.IsolatedAsyncioTestCase):
    async def test_mount(self):
        """Test that the tab mounts correctly and widgets exist."""
        app = ProxyTestApp()
        async with app.run_test(size=(800, 600)) as pilot:
            # We use pilot to wait for ready
            await pilot.pause()
            self.assertIsNotNone(app.query_one("#proxy-host"))
            self.assertIsNotNone(app.query_one("#proxy-port"))
            self.assertIsNotNone(app.query_one("#btn-proxy-start"))
            self.assertIsNotNone(app.query_one("#proxy-log"))

    async def test_start_proxy_ui(self):
        """Test that clicking start updates UI state."""
        app = ProxyTestApp()

        with patch('shared.tui_proxy.ProxyLabManager') as MockManager:
            # We don't need the return value, just checking calls
            # mock_instance = MockManager.return_value

            async with app.run_test(size=(800, 600)) as pilot:
                # Initial state
                btn = app.query_one("#btn-proxy-start")
                self.assertFalse(btn.disabled)

                # Simulate click event directly
                pilot.app.post_message(Button.Pressed(btn))
                await pilot.pause()

                # Verify button disabled immediately (optimistic UI update)
                self.assertTrue(btn.disabled)

                # Verify manager instantiated
                MockManager.assert_called()


if __name__ == '__main__':
    unittest.main()
