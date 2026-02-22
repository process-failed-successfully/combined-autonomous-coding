import unittest
import asyncio
from unittest.mock import MagicMock, patch
from pathlib import Path
from textual.app import App
from shared.tui_http_server import HttpServerLabTab

class TestApp(App):
    def compose(self):
        yield HttpServerLabTab(project_dir=Path("."))

class TestHttpServerLabTab(unittest.IsolatedAsyncioTestCase):
    async def test_mount(self):
        app = TestApp()
        async with app.run_test() as pilot:
            tab = pilot.app.query_one(HttpServerLabTab)
            self.assertIsNotNone(tab)
            self.assertIsNotNone(tab.query_one("#http-server-port"))
            self.assertIsNotNone(tab.query_one("#btn-http-start"))

    async def test_start_stop(self):
        app = TestApp()

        # Patch the manager inside the module
        with patch('shared.tui_http_server.HttpServerManager') as MockManager:
            # Mock instance
            mock_instance = MockManager.return_value
            mock_instance.start_server = MagicMock()
            mock_instance.stop_server = MagicMock()

            async with app.run_test() as pilot:
                # Start
                await pilot.click("#btn-http-start")
                mock_instance.start_server.assert_called_once()

                start_btn = pilot.app.query_one("#btn-http-start")
                stop_btn = pilot.app.query_one("#btn-http-stop")

                self.assertTrue(start_btn.disabled)
                self.assertFalse(stop_btn.disabled)

                # Stop
                await pilot.click("#btn-http-stop")

                # Wait for background thread to update UI
                # Since we mocked stop_server, the thread finishes fast.
                # But we need to give loop time to process call_from_thread
                await asyncio.sleep(0.5)

                # Verify stop called
                mock_instance.stop_server.assert_called_once()

                # Check UI reset
                self.assertFalse(start_btn.disabled)
                self.assertTrue(stop_btn.disabled)
