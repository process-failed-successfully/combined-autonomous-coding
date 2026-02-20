import json
import threading
from pathlib import Path
from typing import Optional

import requests  # type: ignore
from rich.syntax import Syntax
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (Button, Input, Label, ListItem, ListView, RichLog,
                             TabbedContent, TabPane)

from shared.webhook_lab import WebhookLabManager


class WebhookRequestItem(ListItem):
    def __init__(self, *children, request_id: str, **kwargs) -> None:
        super().__init__(*children, **kwargs)
        self.request_id = request_id


class WebhookLabTab(Container):
    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = WebhookLabManager(project_dir, quiet=True)
        self.server_running = False
        self.selected_request_id: Optional[str] = None

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Webhook Lab[/bold]", classes="welcome-text")

            # Controls
            with Horizontal(classes="stat-box"):
                yield Label("Port:")
                yield Input("8080", id="wh-port", classes="short-input")
                yield Label("Forward URL:")
                yield Input(placeholder="http://example.com/api", id="wh-forward")
                yield Button("Start Server", id="btn-wh-start", variant="primary")
                yield Button("Stop Server", id="btn-wh-stop", variant="error", disabled=True)
                yield Label("Stopped", id="lbl-wh-status", classes="status-disconnected")

            with Horizontal():
                # Request List
                with Vertical(id="wh-list-container", classes="stat-box"):
                    yield Label("[bold]Incoming Requests[/bold]")
                    yield ListView(id="wh-list")
                    yield Button("Clear History", id="btn-wh-clear", variant="default")

                # Details
                with Vertical(id="wh-details-container"):
                    yield Label("[bold]Request Details[/bold]")
                    with TabbedContent():
                        with TabPane("Summary"):
                            yield RichLog(id="wh-summary-log", markup=True)
                        with TabPane("Headers"):
                            yield RichLog(id="wh-headers-log", markup=True)
                        with TabPane("Body"):
                            yield RichLog(id="wh-body-log", markup=True)

                    with Horizontal(classes="stat-box"):
                        yield Label("Replay Target:")
                        yield Input(placeholder="http://localhost:8080", id="wh-replay-target")
                        yield Button("Replay Request", id="btn-wh-replay", variant="warning", disabled=True)

    def on_mount(self) -> None:
        self.set_interval(1.0, self.poll_requests)
        self.refresh_list()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-wh-start":
            self.start_server()
        elif event.button.id == "btn-wh-stop":
            self.stop_server()
        elif event.button.id == "btn-wh-clear":
            self.clear_history()
        elif event.button.id == "btn-wh-replay":
            self.replay_request()

    def start_server(self) -> None:
        port_str = self.query_one("#wh-port", Input).value
        try:
            port = int(port_str)
        except ValueError:
            self.notify("Invalid port.", severity="error")
            return

        forward_url = self.query_one("#wh-forward", Input).value or None

        try:
            self.manager.start_server(port, forward_url, blocking=False)
            self.server_running = True
            self.update_ui_state(True)
            self.notify(f"Server started on port {port}.")
        except Exception as e:
            self.notify(f"Error starting server: {e}", severity="error")

    def stop_server(self) -> None:
        try:
            self.manager.stop_server()
            self.server_running = False
            self.update_ui_state(False)
            self.notify("Server stopped.")
        except Exception as e:
            self.notify(f"Error stopping server: {e}", severity="error")

    def on_unmount(self) -> None:
        # Ensure server is stopped when tab is closed/unmounted
        if self.server_running:
            self.manager.stop_server()

    def update_ui_state(self, running: bool) -> None:
        self.query_one("#btn-wh-start").disabled = running
        self.query_one("#btn-wh-stop").disabled = not running
        self.query_one("#wh-port").disabled = running
        self.query_one("#wh-forward").disabled = running

        lbl = self.query_one("#lbl-wh-status", Label)
        if running:
            lbl.update("Running")
            lbl.remove_class("status-disconnected")
            lbl.add_class("status-connected")
        else:
            lbl.update("Stopped")
            lbl.remove_class("status-connected")
            lbl.add_class("status-disconnected")

    def poll_requests(self) -> None:
        # Check if list needs update
        current_count = len(self.query_one("#wh-list", ListView).children)
        if len(self.manager.requests) != current_count:
            self.refresh_list()

    def refresh_list(self) -> None:
        list_view = self.query_one("#wh-list", ListView)
        list_view.clear()

        # Latest on top
        for req in reversed(self.manager.requests):
            method = req['method']
            path = req['path']
            # safely extract time if format matches ISO
            time_str = req['timestamp']
            if "T" in time_str:
                time_str = time_str.split("T")[1][:8]

            label = f"[{time_str}] {method} {path}"
            item = WebhookRequestItem(Label(label), request_id=req['id'])
            list_view.append(item)

    @on(ListView.Selected, "#wh-list")
    def on_request_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, WebhookRequestItem):
            self.selected_request_id = event.item.request_id
            self.show_details(self.selected_request_id)
            self.query_one("#btn-wh-replay").disabled = False

    def show_details(self, req_id: Optional[str]) -> None:
        if not req_id:
            return

        req = next((r for r in self.manager.requests if r['id'] == req_id), None)
        if not req:
            return

        # Summary
        summary = self.query_one("#wh-summary-log", RichLog)
        summary.clear()
        summary.write(f"[bold]ID:[/bold] {req['id']}")
        summary.write(f"[bold]Time:[/bold] {req['timestamp']}")
        summary.write(f"[bold]Method:[/bold] {req['method']}")
        summary.write(f"[bold]Path:[/bold] {req['path']}")

        # Headers
        headers = self.query_one("#wh-headers-log", RichLog)
        headers.clear()
        for k, v in req['headers'].items():
            headers.write(f"[cyan]{k}[/cyan]: {v}")

        # Body
        body_log = self.query_one("#wh-body-log", RichLog)
        body_log.clear()
        body = req.get('body', '')
        if body:
            try:
                # Try format JSON
                json_obj = json.loads(body)
                body_log.write(Syntax(json.dumps(json_obj, indent=2), "json"))
            except Exception:
                body_log.write(body)
        else:
            body_log.write("[dim](empty)[/dim]")

    def clear_history(self) -> None:
        self.manager.requests = []
        self.refresh_list()
        self.query_one("#wh-summary-log", RichLog).clear()
        self.query_one("#wh-headers-log", RichLog).clear()
        self.query_one("#wh-body-log", RichLog).clear()
        self.query_one("#btn-wh-replay").disabled = True

    def replay_request(self) -> None:
        if not self.selected_request_id:
            return

        target = self.query_one("#wh-replay-target", Input).value
        if not target:
            self.notify("Replay target required.", severity="error")
            return

        self.notify(f"Replaying {self.selected_request_id} to {target}...")

        req = next((r for r in self.manager.requests if r['id'] == self.selected_request_id), None)
        if req:
            headers = {k: v for k, v in req['headers'].items()
                       if k.lower() not in ['host', 'content-length', 'content-type']}
            if 'Content-Type' in req['headers']:
                headers['Content-Type'] = req['headers']['Content-Type']
            elif 'content-type' in req['headers']:
                headers['Content-Type'] = req['headers']['content-type']

            # Run in thread
            def do_replay():
                try:
                    resp = requests.request(
                        method=req['method'],
                        url=target,
                        headers=headers,
                        data=req['body'].encode('utf-8'),
                        timeout=10
                    )
                    self.app.call_from_thread(self.notify, f"Replay: {resp.status_code}")
                except Exception as e:
                    self.app.call_from_thread(self.notify, f"Replay failed: {e}", severity="error")

            threading.Thread(target=do_replay, daemon=True).start()
