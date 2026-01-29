import unittest
import threading
import http.client
import http.server
import json
import time
import shutil
import tempfile
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
from shared.mock_server import MockRequestHandler
from shared.config import Config

class TestMockServer(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        # Use a random-ish port or just hope 8889 is free.
        # Better to let OS pick port by binding to 0, but then we need to read it back.
        self.server = None
        self.server_thread = None

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
        self.server = http.server.ThreadingHTTPServer(("localhost", 0), handler_factory)
        self.port = self.server.server_port

        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        time.sleep(0.1) # Wait for server to start

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

        conn = http.client.HTTPConnection("localhost", self.port)
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

        conn = http.client.HTTPConnection("localhost", self.port)
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

        self.start_server({}) # Empty config

        conn = http.client.HTTPConnection("localhost", self.port)
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
