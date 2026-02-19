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

class TestShutdown(unittest.TestCase):
    def test_shutdown_with_open_connection(self):
        origin_port = get_free_port()
        proxy_port = get_free_port()

        # Origin
        origin_server = socketserver.TCPServer(("127.0.0.1", origin_port), MockOriginHandler)
        origin_thread = threading.Thread(target=origin_server.serve_forever)
        origin_thread.daemon = True
        origin_thread.start()

        # Proxy
        proxy_manager = ProxyLabManager(port=proxy_port, host="127.0.0.1")
        proxy_thread = threading.Thread(target=proxy_manager.start)
        proxy_thread.daemon = True
        proxy_thread.start()

        time.sleep(1)

        # Make a request but keep connection open?
        # requests.get uses a context manager so it should be fine.

        proxies = {"http": f"http://127.0.0.1:{proxy_port}"}
        requests.get(f"http://127.0.0.1:{origin_port}", proxies=proxies)

        # Now try to stop
        start_time = time.time()
        proxy_manager.stop()
        duration = time.time() - start_time

        print(f"Shutdown took {duration:.4f}s")

        origin_server.shutdown()
        origin_server.server_close()

if __name__ == "__main__":
    unittest.main()
