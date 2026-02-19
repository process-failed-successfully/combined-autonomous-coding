import sys
import http.server
import socketserver
import socket
import select
import threading
import logging
import time
import requests
from urllib.parse import urlparse
from typing import Optional, List, Tuple
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("proxy-lab")

try:
    from rich.console import Console
    from rich.text import Text
    from rich.highlighter import ReprHighlighter
    from rich.syntax import Syntax
    HAS_RICH = True
    console = Console()
except ImportError:
    HAS_RICH = False
    console = None

class ProxyRequestHandler(http.server.BaseHTTPRequestHandler):
    """
    A simple HTTP Proxy Request Handler.
    Supports standard HTTP methods and CONNECT for HTTPS tunneling.
    """
    protocol_version = "HTTP/1.1"

    def do_GET(self):
        self._proxy_request("GET")

    def do_POST(self):
        self._proxy_request("POST")

    def do_PUT(self):
        self._proxy_request("PUT")

    def do_DELETE(self):
        self._proxy_request("DELETE")

    def do_HEAD(self):
        self._proxy_request("HEAD")

    def do_OPTIONS(self):
        self._proxy_request("OPTIONS")

    def do_PATCH(self):
        self._proxy_request("PATCH")

    def _proxy_request(self, method):
        """
        Proxies the HTTP request to the target server.
        """
        start_time = time.time()
        url = self.path

        # Parse headers
        headers = {k: v for k, v in self.headers.items()}

        # Handle Host header
        parsed_url = urlparse(url)
        if parsed_url.netloc:
             headers["Host"] = parsed_url.netloc

        # Read body if present
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else None

        self._log_request(method, url)

        try:
            # Forward the request
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                data=body,
                allow_redirects=False, # We want to pass redirects back to client
                stream=True, # Stream response content
                timeout=30
            )

            # Read full content to avoid Content-Length mismatches (decompression)
            # requests auto-decompresses gzip/deflate by default
            content = response.content

            # Send response status line
            self.send_response(response.status_code)

            # Forward response headers
            # Filter out hop-by-hop headers and Content-Length/Encoding (recalculated)
            hop_by_hop = [
                'connection', 'keep-alive', 'proxy-authenticate',
                'proxy-authorization', 'te', 'trailers',
                'transfer-encoding', 'upgrade',
                'content-length', 'content-encoding'
            ]

            for key, value in response.headers.items():
                if key.lower() not in hop_by_hop:
                    self.send_header(key, value)

            # Send new Content-Length
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()

            # Write body
            self.wfile.write(content)

            duration = time.time() - start_time
            self._log_response(response.status_code, duration, len(content))

        except requests.exceptions.RequestException as e:
            self.send_error(502, f"Proxy Error: {e}")
            self._log_error(f"Request failed: {e}")
        except Exception as e:
            self.send_error(500, f"Internal Proxy Error: {e}")
            self._log_error(f"Internal error: {e}")

    def do_CONNECT(self):
        """
        Handles HTTPS tunneling via CONNECT method.
        """
        start_time = time.time()
        address = self.path.split(':')
        if len(address) == 2:
            host, port = address[0], int(address[1])
        else:
            host, port = address[0], 443

        self._log_request("CONNECT", self.path)

        try:
            # Connect to destination
            remote_socket = socket.create_connection((host, port), timeout=30)

            # Send 200 OK to client
            self.send_response(200, "Connection Established")
            self.end_headers()

            # Tunnel data
            self._tunnel(self.connection, remote_socket)

            duration = time.time() - start_time
            self._log_response(200, duration, "tunnel")

        except Exception as e:
            self.send_error(502, f"CONNECT failed: {e}")
            self._log_error(f"CONNECT failed: {e}")

    def _tunnel(self, client_socket, remote_socket):
        """
        Bidirectional data transfer between client and remote sockets.
        """
        sockets = [client_socket, remote_socket]
        try:
            while True:
                readable, _, _ = select.select(sockets, [], [], 60)
                if not readable:
                    break

                for s in readable:
                    other = remote_socket if s is client_socket else client_socket
                    data = s.recv(8192)
                    if not data:
                        return
                    other.sendall(data)
        except Exception:
            pass
        finally:
            client_socket.close()
            remote_socket.close()

    def _log_request(self, method, url):
        if HAS_RICH and console:
            console.print(f"[bold cyan]{method}[/bold cyan] [blue]{url}[/blue]")
        else:
            logger.info(f"{method} {url}")

    def _log_response(self, status, duration, size):
        color = "green" if 200 <= status < 300 else "yellow" if 300 <= status < 400 else "red"
        if HAS_RICH and console:
            console.print(f"  -> [{color}]{status}[/{color}] ({duration:.3f}s, size: {size})")
        else:
            logger.info(f"  -> {status} ({duration:.3f}s, size: {size})")

    def _log_error(self, message):
        if HAS_RICH and console:
            console.print(f"[bold red]Error:[/bold red] {message}")
        else:
            logger.error(f"Error: {message}")

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    """Handle requests in a separate thread."""
    daemon_threads = True

class ProxyLabManager:
    def __init__(self, port: int = 8080, host: str = "127.0.0.1"):
        self.port = port
        self.host = host
        self.server = None
        self.thread = None

    def start(self):
        """Starts the proxy server."""
        try:
            self.server = ThreadedHTTPServer((self.host, self.port), ProxyRequestHandler)
            # Update port if allocated dynamically
            if self.port == 0:
                self.port = self.server.server_address[1]

            print(f"✅ Proxy Lab listening on {self.host}:{self.port}")
            print("Configure your browser or tools to use this proxy.")
            print("Press Ctrl+C to stop.")

            self.server.serve_forever()
        except OSError as e:
            print(f"❌ Error starting server: {e}")
            raise # Raise exception instead of sys.exit to allow caller to handle
        except KeyboardInterrupt:
            print("\nStopping proxy...")
            self.stop()

    def stop(self):
        """Stops the proxy server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()

def run_proxy_lab_logic(args):
    """CLI logic for Proxy Lab."""
    manager = ProxyLabManager(port=args.port, host=args.host)
    manager.start()
