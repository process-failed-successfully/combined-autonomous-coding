import http.server
import socketserver
import threading
import ssl
import time
import random
import base64
import os
import sys
import shutil
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

class StaticLabHandler(http.server.SimpleHTTPRequestHandler):
    """
    Advanced Static File Handler with testing capabilities.
    """
    def __init__(self, *args, config: Dict[str, Any], **kwargs):
        self.config = config
        # directory argument is available in Python 3.7+
        super().__init__(*args, directory=self.config.get("directory", "."), **kwargs)

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        if self.config.get("cors"):
            self.send_response(200)
            self.end_headers()
        else:
            self.send_error(501, "Unsupported method ('OPTIONS')")

    def do_GET(self):
        """Handle GET requests with simulated conditions."""
        if not self._check_auth():
            return

        self._simulate_network_conditions()

        if self._should_error():
            self.send_error(500, "Simulated Internal Server Error")
            return

        # SPA Mode: If file doesn't exist, serve index.html
        if self.config.get("spa"):
            path = self.translate_path(self.path)
            if not os.path.exists(path) or os.path.isdir(path):
                # Check if it's a directory that has an index.html, that's fine
                # But if it's a missing file, serve root index.html
                # simple logic: if path doesn't exist, serve /index.html
                if not os.path.exists(path):
                    self.path = "/index.html"

        super().do_GET()

    def do_POST(self):
        """Handle POST requests (uploads)."""
        if not self._check_auth():
            return

        self._simulate_network_conditions()

        if self._should_error():
            self.send_error(500, "Simulated Internal Server Error")
            return

        upload_dir = self.config.get("upload_dir")
        if upload_dir:
            self._handle_upload(upload_dir)
        else:
            self.send_error(405, "Method Not Allowed (Uploads disabled)")

    def end_headers(self):
        """Add CORS headers."""
        if self.config.get("cors"):
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "*")
        super().end_headers()

    def _check_auth(self) -> bool:
        """Verifies Basic Auth."""
        auth_config = self.config.get("auth")
        if not auth_config:
            return True

        auth_header = self.headers.get("Authorization")
        if not auth_header:
            self.send_response(401)
            self.send_header("WWW-Authenticate", 'Basic realm="Static Lab"')
            self.end_headers()
            return False

        try:
            auth_type, encoded = auth_header.split(" ", 1)
            if auth_type.lower() != "basic":
                self.send_error(401, "Invalid Auth Type")
                return False

            decoded = base64.b64decode(encoded).decode("utf-8")
            if decoded == auth_config:
                return True
        except Exception:
            pass

        self.send_error(401, "Invalid Credentials")
        return False

    def _simulate_network_conditions(self):
        """Applies artificial delay."""
        delay = self.config.get("delay", 0)
        if delay > 0:
            time.sleep(delay)

    def _should_error(self) -> bool:
        """Determines if a random error should be injected."""
        rate = self.config.get("error_rate", 0)
        if rate > 0:
            return random.random() < rate
        return False

    def _handle_upload(self, upload_dir: str):
        """Saves uploaded files."""
        # This is a basic implementation. For robust upload handling,
        # we'd need to parse multipart/form-data.
        # SimpleHTTPRequestHandler doesn't do this out of the box.
        # We'll save the raw body for now or try to parse simple binary uploads.

        # If Content-Type is multipart, it's complex.
        # If it's raw binary, we save it.

        length = int(self.headers.get('Content-Length', 0))
        if length > 10 * 1024 * 1024: # 10MB limit
             self.send_error(413, "Payload Too Large")
             return

        content = self.rfile.read(length)

        filename = f"upload_{int(time.time())}.bin"
        # Try to find filename in Content-Disposition if present
        # Content-Disposition: form-data; name="file"; filename="test.txt"
        disposition = self.headers.get("Content-Disposition")
        if disposition:
            import re
            m = re.search(r'filename="([^"]+)"', disposition)
            if m:
                filename = m.group(1)
                # Sanitize filename
                filename = os.path.basename(filename)

        path = Path(upload_dir) / filename
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(path, "wb") as f:
                f.write(content)

            self.send_response(201)
            self.end_headers()
            self.wfile.write(b"Upload received.")
        except Exception as e:
            self.send_error(500, f"Failed to save file: {e}")


class StaticLabManager:
    """Manages the lifecycle of the Static Lab server."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.httpd: Optional[http.server.ThreadingHTTPServer] = None
        self.thread = None

    def run(self):
        """Starts the server (blocking)."""
        port = self.config.get("port", 8000)
        host = self.config.get("host", "0.0.0.0")  # nosec B104

        # Factory for handler
        def handler_factory(*args, **kwargs):
            return StaticLabHandler(*args, config=self.config, **kwargs)

        self.httpd = http.server.ThreadingHTTPServer((host, port), handler_factory)

        # SSL Support
        if self.config.get("ssl"):
            self._setup_ssl()

        print(f"--- Static Lab Server ---")
        print(f"Serving: {self.config.get('directory', '.')}")
        print(f"URL: {'https' if self.config.get('ssl') else 'http'}://{host}:{port}")

        if self.config.get("cors"):
            print("CORS: Enabled")
        if self.config.get("delay"):
            print(f"Latency: {self.config['delay']}s")
        if self.config.get("error_rate"):
            print(f"Error Rate: {self.config['error_rate']:.1%}")
        if self.config.get("auth"):
            print("Auth: Enabled")
        if self.config.get("upload_dir"):
            print(f"Uploads: {self.config['upload_dir']}")
        if self.config.get("spa"):
            print("SPA Mode: Enabled")

        try:
            if self.httpd:
                self.httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def _setup_ssl(self):
        """Generates self-signed cert and wraps socket."""
        # Import here to avoid circular dependency issues if shared.cert_lab isn't ready
        # But we assume it exists.
        # Alternatively, use a temp cert generation logic.

        # We will use a temporary cert file
        import tempfile
        import atexit

        # Use CertLabManager if available, else basic generation
        try:
            from shared.cert_lab import CertLabManager
            manager = CertLabManager()
            # We need a directory to store the cert
            cert_dir = Path(tempfile.mkdtemp())
            cert_path, key_path = manager.generate_self_signed(
                common_name="localhost",
                sans=["localhost", "127.0.0.1"],
                days=1,
                output_dir=cert_dir
            )

            # Register cleanup
            def cleanup():
                shutil.rmtree(cert_dir, ignore_errors=True)
            atexit.register(cleanup)

        except ImportError:
            print("Warning: CertLabManager not found. SSL requires manual certs or CertLab.", file=sys.stderr)
            return

        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile=cert_path, keyfile=key_path)
        if self.httpd:
            self.httpd.socket = context.wrap_socket(self.httpd.socket, server_side=True)

    def stop(self):
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
            print("\nServer stopped.")


def run_static_lab_logic(args):
    """CLI Entry point."""
    config = {
        "port": args.port,
        "directory": args.dir,
        "cors": args.cors,
        "delay": args.delay,
        "error_rate": args.error_rate,
        "auth": args.auth,
        "upload_dir": args.upload,
        "spa": args.spa,
        "ssl": args.ssl
    }

    manager = StaticLabManager(config)
    manager.run()
