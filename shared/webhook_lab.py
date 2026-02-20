import json
import sys
import time
import requests  # type: ignore
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional, Dict, List, Any, cast
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax


class WebhookServer(ThreadingHTTPServer):
    manager: "WebhookLabManager"


class WebhookRequestHandler(BaseHTTPRequestHandler):
    """
    Handles incoming webhook requests.
    """

    def _handle_request(self, method):
        # 1. Capture basic info
        timestamp = datetime.now().isoformat()
        path = self.path
        headers = dict(self.headers)

        # 2. Read body
        content_length = int(headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8', errors='replace')

        server = cast(WebhookServer, self.server)

        # 3. Log request
        server.manager.log_request(timestamp, method, path, headers, body)

        # 4. Forward if configured
        forward_url = server.manager.forward_url
        response_status = 200
        response_body = b"Webhook received."
        response_headers = {"Content-Type": "text/plain"}

        if forward_url:
            try:
                # Construct target URL
                target = forward_url

                # Forward request
                forward_headers = {k: v for k, v in headers.items() if k.lower() not in ['host', 'content-length']}

                resp = requests.request(
                    method=method,
                    url=target,
                    headers=forward_headers,
                    data=body.encode('utf-8'),
                    timeout=10
                )

                response_status = resp.status_code
                response_body = resp.content
                response_headers = dict(resp.headers)

                server.manager.log_message(f"[dim]Forwarded to {target}: {resp.status_code}[/dim]")

            except Exception as e:
                server.manager.log_message(f"[red]Error forwarding to {forward_url}: {e}[/red]")
                response_status = 502
                response_body = f"Error forwarding: {e}".encode('utf-8')

        # 5. Send response
        self.send_response(response_status)
        for k, v in response_headers.items():
            if k.lower() not in ['content-encoding', 'content-length', 'transfer-encoding']:
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(response_body)

    def do_GET(self):
        self._handle_request("GET")

    def do_POST(self):
        self._handle_request("POST")

    def do_PUT(self):
        self._handle_request("PUT")

    def do_DELETE(self):
        self._handle_request("DELETE")

    def do_PATCH(self):
        self._handle_request("PATCH")

    def do_HEAD(self):
        self._handle_request("HEAD")

    def do_OPTIONS(self):
        self._handle_request("OPTIONS")

    def log_message(self, format, *args):
        # Silence default logging
        pass


class WebhookLabManager:
    def __init__(self, project_dir: Path, quiet: bool = False):
        self.project_dir = project_dir
        self.history_file = project_dir / ".webhook_history.jsonl"
        self.console = Console()
        self.forward_url: Optional[str] = None
        self.server: Optional[WebhookServer] = None
        self.server_thread: Optional[threading.Thread] = None
        self.requests: List[Dict[str, Any]] = []  # In-memory cache
        self.quiet = quiet
        self.load_history()

    def log_message(self, message: str):
        if not self.quiet:
            self.console.print(message)

    def load_history(self):
        """Loads recent history from file into memory."""
        if not self.history_file.exists():
            return

        try:
            with open(self.history_file, 'r') as f:
                for line in f:
                    if line.strip():
                        self.requests.append(json.loads(line))
        except Exception as e:
            self.log_message(f"[red]Error reading history: {e}[/red]")

    def start_server(self, port: int, forward_url: Optional[str] = None, blocking: bool = True):
        self.forward_url = forward_url

        # Use localhost to avoid binding to all interfaces (Bandit security check)
        self.server = WebhookServer(('127.0.0.1', port), WebhookRequestHandler)
        self.server.manager = self  # Inject manager

        self.log_message(f"[bold green]Webhook Lab listening on 127.0.0.1:{port}...[/bold green]")
        if forward_url:
            self.log_message(f"[cyan]Forwarding requests to: {forward_url}[/cyan]")
        self.log_message(f"[dim]Saving requests to: {self.history_file}[/dim]")

        if blocking:
            self.log_message("Press Ctrl+C to stop.\n")
            try:
                self.server.serve_forever()
            except KeyboardInterrupt:
                self.log_message("\n[bold red]Stopping server...[/bold red]")
                self.server.shutdown()
        else:
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()

    def stop_server(self):
        if self.server:
            self.log_message("Stopping server...")
            self.server.shutdown()
            self.server.server_close()
            self.server = None
            if self.server_thread:
                self.server_thread.join()
                self.server_thread = None
            self.log_message("Server stopped.")

    def log_request(self, timestamp: str, method: str, path: str, headers: Dict[str, Any], body: str) -> str:
        """
        Logs request to console and file. Returns generated ID.
        """
        # Generate simple ID (timestamp + counter? or just hex timestamp)
        req_id = hex(int(time.time() * 1000))[2:]

        entry = {
            "id": req_id,
            "timestamp": timestamp,
            "method": method,
            "path": path,
            "headers": headers,
            "body": body
        }

        self.requests.append(entry)

        # Console Output
        self.log_message(f"[bold]{method} {path}[/bold] (ID: {req_id})")

        # Save to file
        with open(self.history_file, 'a') as f:
            f.write(json.dumps(entry) + "\n")

        return req_id

    def list_requests(self, limit: int = 10):
        # Use in-memory cache if available, otherwise reload
        # But we keep cache synced.
        entries = self.requests[-limit:]

        table = Table(title=f"Recent Webhooks (Last {len(entries)})")
        table.add_column("ID", style="cyan")
        table.add_column("Timestamp", style="dim")
        table.add_column("Method", style="bold")
        table.add_column("Path")
        table.add_column("Size")

        for e in entries:
            size = len(e.get('body', ''))
            table.add_row(
                e['id'],
                e['timestamp'],
                e['method'],
                e['path'],
                f"{size} bytes"
            )

        self.console.print(table)

    def show_request(self, req_id: str):
        target = next((r for r in self.requests if r['id'] == req_id), None)

        if not target:
            self.console.print(f"[red]Request {req_id} not found.[/red]")
            return

        self.console.print(f"[bold]Request Details: {req_id}[/bold]")
        self.console.print(f"Time: {target['timestamp']}")
        self.console.print(f"URL: {target['method']} {target['path']}")

        # Headers
        table = Table(title="Headers", box=None)
        table.add_column("Key", style="cyan")
        table.add_column("Value")
        for k, v in target['headers'].items():
            table.add_row(k, v)
        self.console.print(table)

        # Body
        self.console.print("\n[bold]Body:[/bold]")
        body = target.get('body', '')
        if not body:
            self.console.print("(empty)")
        else:
            # Try parsing JSON
            try:
                json_obj = json.loads(body)
                self.console.print(Syntax(json.dumps(json_obj, indent=2), "json"))
            except Exception:
                self.console.print(body)

    def replay_request(self, req_id: str, target_url: str):
        target = next((r for r in self.requests if r['id'] == req_id), None)

        if not target:
            self.console.print(f"[red]Request {req_id} not found.[/red]")
            return

        self.console.print(f"Replaying request {req_id} to {target_url}...")

        try:
            # Filter headers
            headers = {k: v for k, v in target['headers'].items()
                       if k.lower() not in ['host', 'content-length', 'content-type']}

            # Re-add Content-Type if present in original (it's important)
            if 'Content-Type' in target['headers']:
                headers['Content-Type'] = target['headers']['Content-Type']
            elif 'content-type' in target['headers']:
                headers['Content-Type'] = target['headers']['content-type']

            resp = requests.request(
                method=target['method'],
                url=target_url,
                headers=headers,
                data=target['body'].encode('utf-8'),
                timeout=10
            )

            status_color = "green" if resp.ok else "red"
            self.console.print(f"[{status_color}]Status: {resp.status_code} {resp.reason}[/{status_color}]")
            self.console.print(f"Response Body: {len(resp.content)} bytes")

        except Exception as e:
            self.console.print(f"[red]Error replaying request: {e}[/red]")


def run_webhook_lab_logic(args):
    """
    CLI Entry point for Webhook Lab.
    """
    project_dir = args.project_dir.resolve()
    manager = WebhookLabManager(project_dir)

    if args.action == "listen":
        manager.start_server(args.port, args.forward)

    elif args.action == "list":
        manager.list_requests(args.limit)

    elif args.action == "show":
        manager.show_request(args.id)

    elif args.action == "replay":
        manager.replay_request(args.id, args.target)

    else:
        print(f"Unknown action: {args.action}")
        sys.exit(1)
