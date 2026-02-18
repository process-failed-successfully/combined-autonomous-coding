import unittest
import threading
import time
import requests
import random
import shutil
import tempfile
import os
from pathlib import Path
from shared.static_lab import StaticLabManager

class TestStaticLab(unittest.TestCase):
    def setUp(self):
        # Pick a random port to avoid conflicts
        self.port = random.randint(30000, 40000)
        self.tmp_dir = tempfile.mkdtemp()
        self.upload_dir = tempfile.mkdtemp()
        self.base_url = f"http://localhost:{self.port}"

        # Create a test file
        with open(Path(self.tmp_dir) / "index.html", "w") as f:
            f.write("<h1>Hello World</h1>")

        with open(Path(self.tmp_dir) / "data.json", "w") as f:
            f.write('{"key": "value"}')

    def tearDown(self):
        if hasattr(self, 'manager'):
            self.manager.stop()
            # Wait for server to stop
            if self.server_thread.is_alive():
                self.server_thread.join(timeout=2)

        if os.path.exists(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)
        if os.path.exists(self.upload_dir):
            shutil.rmtree(self.upload_dir)

    def start_server(self, **kwargs):
        config = {
            "port": self.port,
            "directory": self.tmp_dir,
            "host": "localhost",
            **kwargs
        }
        self.manager = StaticLabManager(config)
        self.server_thread = threading.Thread(target=self.manager.run, daemon=True)
        self.server_thread.start()

        # Wait for server to come up
        for _ in range(10):
            try:
                requests.get(self.base_url, timeout=0.1)
                break
            except requests.RequestException:
                time.sleep(0.1)

    def test_serve_static(self):
        self.start_server()
        resp = requests.get(f"{self.base_url}/index.html")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Hello World", resp.text)

    def test_cors(self):
        self.start_server(cors=True)
        resp = requests.options(f"{self.base_url}/data.json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get("Access-Control-Allow-Origin"), "*")

        resp = requests.get(f"{self.base_url}/data.json")
        self.assertEqual(resp.headers.get("Access-Control-Allow-Origin"), "*")

    def test_latency(self):
        # 0.5s delay
        self.start_server(delay=0.5)
        start = time.time()
        requests.get(f"{self.base_url}/index.html")
        elapsed = time.time() - start
        # Allow small margin of error (it takes at least 0.5s)
        self.assertGreaterEqual(elapsed, 0.5)

    def test_error_rate(self):
        # 100% error rate
        self.start_server(error_rate=1.0)
        resp = requests.get(f"{self.base_url}/index.html")
        self.assertEqual(resp.status_code, 500)

    def test_auth(self):
        user = "admin"
        pw = "secret"
        self.start_server(auth=f"{user}:{pw}")

        # No auth
        resp = requests.get(f"{self.base_url}/index.html")
        self.assertEqual(resp.status_code, 401)

        # Wrong auth
        resp = requests.get(f"{self.base_url}/index.html", auth=("admin", "wrong"))
        self.assertEqual(resp.status_code, 401)

        # Correct auth
        resp = requests.get(f"{self.base_url}/index.html", auth=(user, pw))
        self.assertEqual(resp.status_code, 200)

    def test_spa_mode(self):
        self.start_server(spa=True)

        # Existing file
        resp = requests.get(f"{self.base_url}/data.json")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("key", resp.text)

        # Missing file -> index.html
        resp = requests.get(f"{self.base_url}/missing-route")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Hello World", resp.text)

    def test_upload(self):
        self.start_server(upload_dir=self.upload_dir)

        data = b"Some binary data"
        resp = requests.post(f"{self.base_url}/upload", data=data)
        self.assertEqual(resp.status_code, 201)

        # Check if file exists in upload dir
        files = list(Path(self.upload_dir).glob("*"))
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].read_bytes(), data)

    def test_upload_disabled(self):
        self.start_server() # upload_dir=None
        resp = requests.post(f"{self.base_url}/upload", data=b"data")
        self.assertEqual(resp.status_code, 405)

if __name__ == "__main__":
    unittest.main()
