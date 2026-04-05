import unittest
from unittest.mock import MagicMock, patch
from textual.app import App, ComposeResult
from shared.tui_http import HttpLabTab

# Helper app
class HttpLabTestApp(App):
    def compose(self) -> ComposeResult:
        yield HttpLabTab()

class TestHttpLabTab(unittest.IsolatedAsyncioTestCase):
    async def test_ui_elements(self):
        app = HttpLabTestApp()
        async with app.run_test(size=(300, 50)) as pilot:
            self.assertIsNotNone(app.query_one("#http-url"))
            self.assertIsNotNone(app.query_one("#btn-http-send"))
            self.assertIsNotNone(app.query_one("#http-history-list"))

    @patch("shared.tui_http.HttpLabManager")
    async def test_send_request_success(self, MockManager):
        # Setup mock
        mock_instance = MockManager.return_value
        mock_instance.request.return_value = {
            "status_code": 200,
            "elapsed": 0.5,
            "ok": True,
            "headers": {"Content-Type": "application/json"},
            "body": '{"foo": "bar"}',
            "json": {"foo": "bar"}
        }

        app = HttpLabTestApp()
        # Use a larger screen size to ensure widgets are visible
        async with app.run_test(size=(300, 50)) as pilot:
            tab = app.query_one(HttpLabTab)

            # Override the manager instance that was created in __init__
            tab.manager = mock_instance

            # Fill inputs
            tab.query_one("#http-url").value = "https://api.example.com"

            # Click send
            app.query_one("#btn-http-send").press()
        await pilot.pause()

            # Wait for any events
            await pilot.pause()

            # Check if request was called
            mock_instance.request.assert_called_with("GET", "https://api.example.com", headers={}, timeout=10.0)

            # Check UI update (Status label)
            lbl = tab.query_one("#http-status-lbl")
            self.assertIn("200", str(lbl.render()))

    @patch("shared.tui_http.HttpLabManager")
    async def test_import_curl(self, MockManager):
        mock_instance = MockManager.return_value
        mock_instance.parse_curl.return_value = {
            "url": "https://api.example.com",
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "data": '{"test": 123}'
        }

        app = HttpLabTestApp()
        async with app.run_test(size=(300, 50)) as pilot:
            tab = app.query_one(HttpLabTab)
            tab.manager = mock_instance

            # Fill inputs
            tab.query_one("#http-curl-input").value = "curl -X POST https://api.example.com -d '{\"test\": 123}'"

            # Click import
            app.query_one("#btn-http-import-curl").press()
        await pilot.pause()
            await pilot.pause()

            # Verify UI was updated
            self.assertEqual(tab.query_one("#http-url").value, "https://api.example.com")
            self.assertEqual(tab.query_one("#http-method").value, "POST")
            self.assertIn("Content-Type: application/json", tab.query_one("#http-headers").text)
            self.assertIn('"test": 123', tab.query_one("#http-body").text)

    @patch("shared.tui_http.HttpLabManager")
    async def test_send_request_error(self, MockManager):
        mock_instance = MockManager.return_value
        mock_instance.request.side_effect = Exception("Connection Failed")

        app = HttpLabTestApp()
        async with app.run_test(size=(300, 50)) as pilot:
            tab = app.query_one(HttpLabTab)
            tab.manager = mock_instance
            tab.query_one("#http-url").value = "https://fail.com"

            app.query_one("#btn-http-send").press()
        await pilot.pause()
            await pilot.pause()

            # It should show a notification, but checking notifications in test is hard.
            # We can check that the button is re-enabled.
            self.assertFalse(tab.query_one("#btn-http-send").disabled)
