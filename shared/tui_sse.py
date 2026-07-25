import asyncio
import aiohttp
from datetime import datetime
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Input, Label, RichLog, Checkbox

class SseLabTab(Container):
    """Tab for Server-Sent Events (SSE) Client experimentation."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.session: Optional[aiohttp.ClientSession] = None
        self.response: Optional[aiohttp.ClientResponse] = None
        self.listen_task: Optional[asyncio.Task] = None
        self.is_connected = False

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]SSE Lab[/bold]", classes="welcome-text")

            with Horizontal(classes="stat-box"):
                yield Label("URL:", classes="label")
                yield Input(placeholder="http://localhost:8000/stream", id="sse-url", value="")
                yield Button("Connect", id="btn-sse-connect", variant="primary")
                yield Button("Disconnect", id="btn-sse-disconnect", variant="error", disabled=True)
                yield Label("Disconnected", id="lbl-sse-status", classes="status-disconnected")

            with Horizontal(classes="stat-box"):
                yield Checkbox("Auto-scroll", id="chk-sse-autoscroll", value=True)
                yield Button("Clear Log", id="btn-sse-clear", variant="default")

            yield RichLog(id="sse-log", wrap=True, highlight=True, markup=True)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-sse-connect":
            await self.connect()
        elif event.button.id == "btn-sse-disconnect":
            await self.disconnect()
        elif event.button.id == "btn-sse-clear":
            self.query_one("#sse-log", RichLog).clear()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "sse-url":
            await self.connect()

    async def connect(self) -> None:
        url = self.query_one("#sse-url", Input).value
        if not url:
            self.notify("URL required.", severity="error")
            return

        if not url.startswith("http://") and not url.startswith("https://"):
            url = "http://" + url

        self.log_message(f"Connecting to {url}...", "system")
        self.query_one("#btn-sse-connect").disabled = True

        headers = {
            "Accept": "text/event-stream",
            "Cache-Control": "no-cache"
        }

        try:
            self.session = aiohttp.ClientSession(headers=headers)
            self.response = await self.session.get(url)

            if self.response.status != 200:
                self.log_message(f"Connection failed: Status {self.response.status}", "error")
                await self.disconnect()
                return

            self.is_connected = True
            self.update_ui_connected(True)
            self.log_message("Connected!", "success")

            self.listen_task = asyncio.create_task(self.receive_loop())

        except Exception as e:
            self.log_message(f"Connection failed: {e}", "error")
            await self.disconnect()

    async def disconnect(self) -> None:
        if self.listen_task:
            if self.listen_task is not asyncio.current_task():
                self.listen_task.cancel()
                try:
                    await self.listen_task
                except asyncio.CancelledError:
                    pass
            self.listen_task = None

        if self.response:
            self.response.close()
            self.response = None

        if self.session:
            await self.session.close()
            self.session = None

        self.is_connected = False
        self.update_ui_connected(False)
        self.log_message("Disconnected.", "system")
        self.query_one("#btn-sse-connect").disabled = False

    async def receive_loop(self) -> None:
        if not self.response:
            return

        try:
            async for line in self.response.content:
                line_text = line.decode('utf-8').strip()
                if not line_text:
                    continue

                if line_text.startswith("data: "):
                    self.log_message(f"Data: {line_text[6:]}", "rx-data")
                elif line_text.startswith("event: "):
                    self.log_message(f"Event: {line_text[7:]}", "rx-event")
                elif line_text.startswith("id: "):
                    self.log_message(f"ID: {line_text[4:]}", "rx-meta")
                elif line_text.startswith("retry: "):
                    self.log_message(f"Retry: {line_text[7:]}", "rx-meta")
                else:
                    self.log_message(line_text, "rx-other")

        except aiohttp.ClientPayloadError:
            self.log_message("Connection closed by server.", "warning")
            await self.disconnect()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.log_message(f"Receive error: {e}", "error")
            await self.disconnect()

    def update_ui_connected(self, connected: bool) -> None:
        self.query_one("#btn-sse-connect").disabled = connected
        self.query_one("#btn-sse-disconnect").disabled = not connected

        lbl = self.query_one("#lbl-sse-status", Label)
        if connected:
            lbl.update("Connected")
            lbl.remove_class("status-disconnected")
            lbl.add_class("status-connected")
        else:
            lbl.update("Disconnected")
            lbl.remove_class("status-connected")
            lbl.add_class("status-disconnected")

    def log_message(self, message: str, type: str = "info") -> None:
        log = self.query_one("#sse-log", RichLog)
        timestamp = datetime.now().strftime("%H:%M:%S")

        color = "white"
        if type == "rx-data":
            color = "green"
        elif type == "rx-event":
            color = "blue"
        elif type == "rx-meta":
            color = "dim white"
        elif type == "rx-other":
            color = "white"
        elif type == "error":
            color = "red"
        elif type == "warning":
            color = "yellow"
        elif type == "success":
            color = "green"
        elif type == "system":
            color = "dim white"

        prefix = "<< " if type.startswith("rx") else ""

        # Don't bold the meta elements to make data stand out
        bold_start = "[bold]" if type in ["rx-data", "rx-event"] else ""
        bold_end = "[/bold]" if type in ["rx-data", "rx-event"] else ""

        log.write(f"[{timestamp}] [{color}]{prefix}{bold_start}{message}{bold_end}[/{color}]")

        if self.query_one("#chk-sse-autoscroll", Checkbox).value:
            log.scroll_end(animate=False)
