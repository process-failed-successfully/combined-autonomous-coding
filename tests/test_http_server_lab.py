import unittest
import time
import requests
import shutil
import tempfile
from pathlib import Path
from shared.http_server_lab import HttpServerManager

class TestHttpServerManager(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path(tempfile.mkdtemp())
        self.manager = HttpServerManager(self.project_dir)
        self.port = 18080 # Use a high port to avoid conflicts

    def tearDown(self):
        self.manager.stop_server()
        shutil.rmtree(self.project_dir)

    def test_static_server(self):
        # Create a test file
        index = self.project_dir / "index.html"
        index.write_text("Hello World", encoding="utf-8")

        self.manager.start_server(self.port, directory=".", mode="static")

        # Wait for server to start
        time.sleep(1)

        try:
            resp = requests.get(f"http://127.0.0.1:{self.port}/index.html", timeout=1)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.text, "Hello World")
        except Exception as e:
            self.fail(f"Request failed: {e}")

    def test_echo_server(self):
        self.manager.start_server(self.port, mode="echo")

        # Wait for server to start
        time.sleep(1)

        try:
            resp = requests.post(
                f"http://127.0.0.1:{self.port}/api/test",
                json={"foo": "bar"},
                headers={"X-Test": "123"},
                timeout=1
            )
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data["method"], "POST")
            self.assertEqual(data["path"], "/api/test")
            self.assertEqual(data["headers"].get("X-Test"), "123")
            # Body comes as string in my implementation if it's not handled as json explicitly in echo
            self.assertIn('"foo": "bar"', data["body"])
        except Exception as e:
            self.fail(f"Request failed: {e}")

    def test_double_start_error(self):
        self.manager.start_server(self.port)
        time.sleep(0.5)

        # Capture callback
        errors = []
        def cb(msg):
            errors.append(msg)

        # Try starting again
        self.manager.start_server(self.port, callback=cb)

        self.assertIn("Server is already running.", errors)
