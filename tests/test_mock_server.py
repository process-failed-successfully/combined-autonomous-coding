import unittest
import threading
import http.client
import http.server
import json
import time
import shutil
import tempfile
import socket
from pathlib import Path
from unittest.mock import patch, AsyncMock
from shared.mock_server import MockRequestHandler
from shared.config import Config


class TestMockServer(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        self.server = None
        self.server_thread = None
        self.port = 0

    def tearDown(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        if self.server_thread:
            self.server_thread.join()
        shutil.rmtree(self.test_dir)

    def start_server(self, mock_config):
        agent_config = Config(project_dir=self.project_dir, agent_type="gemini", verbose=False)

        def handler_factory(*args, **kwargs):
            return MockRequestHandler(
                *args,
                project_dir=self.project_dir,
                config=mock_config,
                agent_config=agent_config,
                **kwargs
            )

        # Bind to port 0 to let OS assign a free port
        # We use 127.0.0.1 explicitly to avoid issues with localhost resolution (IPv4/IPv6)
        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler_factory)
        self.port = self.server.server_port

        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()

        # Wait for server to be reachable
        self.wait_for_server()

    def wait_for_server(self, timeout=5.0):
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                with socket.create_connection(("127.0.0.1", self.port), timeout=0.1):
                    return
            except (ConnectionRefusedError, socket.timeout, OSError):
                time.sleep(0.1)
        raise RuntimeError(f"Server failed to start on port {self.port} within {timeout} seconds")

    def test_static_route(self):
        config = {
            "routes": [
                {
                    "path": "/static",
                    "method": "GET",
                    "response": {"status": 200, "body": {"foo": "bar"}}
                }
            ]
        }
        self.start_server(config)

        conn = http.client.HTTPConnection("127.0.0.1", self.port)
        conn.request("GET", "/static")
        res = conn.getresponse()

        self.assertEqual(res.status, 200)
        data = json.loads(res.read().decode())
        self.assertEqual(data, {"foo": "bar"})
        conn.close()

    def test_schema_route(self):
        # Create schema file
        schema = {
            "name": {"type": "name"},
            "age": {"type": "int", "min": 18, "max": 99}
        }
        schema_path = self.project_dir / "user_schema.json"
        with open(schema_path, "w") as f:
            json.dump(schema, f)

        config = {
            "routes": [
                {
                    "path": "/user",
                    "method": "GET",
                    "response": {"status": 200, "schema": "user_schema.json"}
                }
            ]
        }
        self.start_server(config)

        conn = http.client.HTTPConnection("127.0.0.1", self.port)
        conn.request("GET", "/user")
        res = conn.getresponse()

        self.assertEqual(res.status, 200)
        data = json.loads(res.read().decode())
        self.assertIn("name", data)
        self.assertIn("age", data)
        self.assertTrue(18 <= data["age"] <= 99)
        conn.close()

    @patch("agents.gemini.GeminiAgent.run_agent_session", new_callable=AsyncMock)
    def test_ai_route(self, mock_run):
        # Mock AI response
        mock_response_text = '```json\n{"status": 201, "body": {"id": 123}}\n```'
        mock_run.return_value = ("success", mock_response_text, [])

        self.start_server({})  # Empty config

        conn = http.client.HTTPConnection("127.0.0.1", self.port)
        conn.request("POST", "/create-user", body=json.dumps({"name": "Test"}).encode("utf-8"))
        res = conn.getresponse()

        self.assertEqual(res.status, 201)
        data = json.loads(res.read().decode())
        self.assertEqual(data, {"id": 123})
        conn.close()

        # Verify prompt contained request info
        args, _ = mock_run.call_args
        prompt = args[0]
        self.assertIn("POST", prompt)
        self.assertIn("/create-user", prompt)
        self.assertIn('"name": "Test"', prompt)


if __name__ == "__main__":
    unittest.main()
