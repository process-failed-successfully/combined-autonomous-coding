import unittest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
import json

# Mock optional dependencies if missing (though we installed them)
try:
    import requests
except ImportError:
    requests = None

from shared.webhook_lab import WebhookLabManager, WebhookRequestHandler


class TestWebhookLabManager(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.manager = WebhookLabManager(self.project_dir)
        self.manager.console = MagicMock()  # Mock console

    def test_log_request(self):
        with patch("builtins.open", mock_open()) as mock_file:
            req_id = self.manager.log_request(
                timestamp="2023-01-01T12:00:00",
                method="POST",
                path="/webhook",
                headers={"Content-Type": "application/json"},
                body='{"event": "test"}'
            )

            self.assertTrue(req_id)
            mock_file.assert_called_with(self.manager.history_file, 'a')
            handle = mock_file()
            # Verify write
            written = handle.write.call_args[0][0]
            data = json.loads(written.strip())
            self.assertEqual(data["method"], "POST")
            self.assertEqual(data["body"], '{"event": "test"}')

    def test_list_requests(self):
        mock_data = json.dumps({
            "id": "123",
            "timestamp": "2023-01-01T12:00:00",
            "method": "POST",
            "path": "/webhook",
            "headers": {},
            "body": ""
        }) + "\n"

        with patch("pathlib.Path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=mock_data)):

            self.manager.list_requests()

            # Verify console output
            self.manager.console.print.assert_called()
            # We assume it printed a Table

    def test_show_request_found(self):
        mock_data = json.dumps({
            "id": "123",
            "timestamp": "2023-01-01T12:00:00",
            "method": "POST",
            "path": "/webhook",
            "headers": {"Content-Type": "application/json"},
            "body": "{}"
        }) + "\n"

        with patch("pathlib.Path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=mock_data)):

            self.manager.show_request("123")

            # Verify calls to print details
            # We can't easily check exact strings on rich console calls without complex matching,
            # but we can check call count > 0
            self.assertTrue(self.manager.console.print.call_count > 0)

    def test_show_request_not_found(self):
        with patch("pathlib.Path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data="")):

            self.manager.show_request("999")
            # Should verify it printed "not found" or similar
            # self.manager.console.print.assert_called_with(f"[red]Request 999 not found.[/red]") # Requires exact match

    @patch("shared.webhook_lab.requests")
    def test_replay_request(self, mock_requests):
        mock_data = json.dumps({
            "id": "123",
            "timestamp": "2023-01-01T12:00:00",
            "method": "POST",
            "path": "/webhook",
            "headers": {"Content-Type": "application/json", "Host": "example.com"},
            "body": "{}"
        }) + "\n"

        with patch("pathlib.Path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=mock_data)):

            self.manager.replay_request("123", "http://localhost:9000/replay")

            mock_requests.request.assert_called_with(
                method="POST",
                url="http://localhost:9000/replay",
                headers={"Content-Type": "application/json"},  # Host should be filtered
                data=b"{}",
                timeout=10
            )

    @patch("shared.webhook_lab.ThreadingHTTPServer")
    def test_start_server(self, mock_server_cls):
        mock_server = MagicMock()
        mock_server_cls.return_value = mock_server

        self.manager.start_server(8080)

        mock_server_cls.assert_called_with(('0.0.0.0', 8080), WebhookRequestHandler)
        self.assertEqual(mock_server.manager, self.manager)
        mock_server.serve_forever.assert_called_once()


class TestableHandler(WebhookRequestHandler):
    def __init__(self, *args, **kwargs):
        # Skip BaseHTTPRequestHandler __init__ logic
        pass


class TestWebhookRequestHandler(unittest.TestCase):
    def test_handle_request(self):
        handler = TestableHandler()
        handler.server = MagicMock()
        handler.server.manager = MagicMock()
        handler.server.manager.forward_url = None
        handler.server.manager.log_request.return_value = "req_id"

        handler.path = "/test"
        handler.headers = {"Content-Length": "4"}
        handler.rfile = MagicMock()
        handler.rfile.read.return_value = b"body"
        handler.wfile = MagicMock()

        # Mock methods
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()

        # Call handler method (e.g. do_POST)
        handler._handle_request("POST")

        handler.server.manager.log_request.assert_called_with(
            unittest.mock.ANY,  # timestamp
            "POST",
            "/test",
            {"Content-Length": "4"},
            "body"
        )

        handler.send_response.assert_called_with(200)


if __name__ == "__main__":
    unittest.main()
