import unittest
import requests  # type: ignore
import time
import shutil
import tempfile
from pathlib import Path
from shared.webhook_lab import WebhookLabManager


class TestWebhookLab(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.manager = WebhookLabManager(self.test_dir, quiet=True)
        self.port = 18080

    def tearDown(self):
        self.manager.stop_server()
        shutil.rmtree(self.test_dir)

    def test_start_stop_server(self):
        self.manager.start_server(self.port, blocking=False)
        time.sleep(1)  # Wait for startup

        # Check if running
        try:
            resp = requests.get(f"http://127.0.0.1:{self.port}")
            self.assertEqual(resp.status_code, 200)
        except requests.ConnectionError:
            self.fail("Server not reachable")

        self.manager.stop_server()
        time.sleep(0.5)

        # Check if stopped
        with self.assertRaises(requests.ConnectionError):
            requests.get(f"http://127.0.0.1:{self.port}")

    def test_log_request(self):
        self.manager.start_server(self.port, blocking=False)
        time.sleep(1)

        payload = {"test": "data"}
        requests.post(f"http://127.0.0.1:{self.port}/api/test", json=payload)

        time.sleep(0.5)  # Wait for processing

        self.assertEqual(len(self.manager.requests), 1)
        req = self.manager.requests[0]
        self.assertEqual(req['method'], 'POST')
        self.assertEqual(req['path'], '/api/test')
        self.assertIn('"test": "data"', req['body'])

        # Check persistence
        history_file = self.test_dir / ".webhook_history.jsonl"
        self.assertTrue(history_file.exists())

        # New manager should load history
        manager2 = WebhookLabManager(self.test_dir, quiet=True)
        self.assertEqual(len(manager2.requests), 1)

    def test_replay_request(self):
        # We can't easily test replay because it prints to console (which we suppressed)
        # and doesn't return value. But we can ensure it doesn't crash.

        # Manually inject request
        req_id = self.manager.log_request("iso-time", "GET", "/", {}, "")

        # Mock requests.request?
        # For now just call it and ensure no exception
        self.manager.replay_request(req_id, f"http://127.0.0.1:{self.port}")


if __name__ == "__main__":
    unittest.main()
