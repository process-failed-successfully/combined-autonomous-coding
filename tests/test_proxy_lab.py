import threading
import time
import requests
import http.server
import socketserver
import unittest
import socket
from shared.proxy_lab import ProxyLabManager

def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

class MockOriginHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Hello from Origin")

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Received: " + body)

class TestProxyLab(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Find free ports - use 0 to let OS allocate
        cls.origin_port = 0 # bind to 0
        cls.proxy_port = 0 # bind to 0

        # Start Origin Server
        # We allow binding to 0, then read address
        cls.origin_server = socketserver.TCPServer(("127.0.0.1", 0), MockOriginHandler)
        cls.origin_port = cls.origin_server.server_address[1] # Get actual port

        cls.origin_thread = threading.Thread(target=cls.origin_server.serve_forever)
        cls.origin_thread.daemon = True
        cls.origin_thread.start()

        # Start Proxy Server
        # Pass port 0
        cls.proxy_manager = ProxyLabManager(port=0, host="127.0.0.1")
        cls.proxy_thread = threading.Thread(target=cls.proxy_manager.start)
        cls.proxy_thread.daemon = True
        cls.proxy_thread.start()

        # Wait for proxy server to be ready and assign port
        timeout = 5
        start_time = time.time()
        while time.time() - start_time < timeout:
            if cls.proxy_manager.server:
                cls.proxy_port = cls.proxy_manager.port
                break
            time.sleep(0.1)

        if cls.proxy_port == 0:
            raise RuntimeError("Proxy server failed to start within timeout")

    @classmethod
    def tearDownClass(cls):
        if cls.origin_server:
            cls.origin_server.shutdown()
            cls.origin_server.server_close()
        if cls.proxy_manager:
            cls.proxy_manager.stop()

    def test_proxy_get(self):
        proxies = {
            "http": f"http://127.0.0.1:{self.proxy_port}",
        }
        url = f"http://127.0.0.1:{self.origin_port}/test"

        try:
            resp = requests.get(url, proxies=proxies, timeout=5)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.text, "Hello from Origin")
        except requests.exceptions.RequestException as e:
            self.fail(f"Request failed: {e}")

    def test_proxy_post(self):
        proxies = {
            "http": f"http://127.0.0.1:{self.proxy_port}",
        }
        url = f"http://127.0.0.1:{self.origin_port}/post"

        try:
            resp = requests.post(url, data="test data", proxies=proxies, timeout=5)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.text, "Received: test data")
        except requests.exceptions.RequestException as e:
            self.fail(f"Request failed: {e}")

if __name__ == '__main__':
    unittest.main()
