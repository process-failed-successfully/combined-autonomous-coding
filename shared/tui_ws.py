import asyncio
from datetime import datetime
from typing import Optional

import websockets
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Input, Label, RichLog, Checkbox


class WsLabTab(Container):
    """Tab for WebSocket Client experimentation."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.recv_task: Optional[asyncio.Task] = None
        self.is_connected = False

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]WebSocket Lab[/bold]", classes="welcome-text")

            # Connection Bar
            with Horizontal(classes="stat-box"):
                yield Label("URL:", classes="label")
                yield Input(placeholder="ws://localhost:8765", id="ws-url", value="ws://echo.websocket.org")
                yield Button("Connect", id="btn-ws-connect", variant="primary")
                yield Button("Disconnect", id="btn-ws-disconnect", variant="error", disabled=True)
                yield Label("Disconnected", id="lbl-ws-status", classes="status-disconnected")

            # Message Area
            with Horizontal(classes="stat-box"):
                yield Input(placeholder="Message to send...", id="ws-input-msg")
                yield Button("Send", id="btn-ws-send", variant="success", disabled=True)
                yield Checkbox("Auto-scroll", id="chk-ws-autoscroll", value=True)
                yield Button("Clear Log", id="btn-ws-clear", variant="default")

            # Log Area
            yield RichLog(id="ws-log", wrap=True, highlight=True, markup=True)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-ws-connect":
            await self.connect()
        elif event.button.id == "btn-ws-disconnect":
            await self.disconnect()
        elif event.button.id == "btn-ws-send":
            await self.send_message()
        elif event.button.id == "btn-ws-clear":
            self.query_one("#ws-log", RichLog).clear()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "ws-url":
            await self.connect()
        elif event.input.id == "ws-input-msg":
            await self.send_message()

    async def connect(self) -> None:
        url = self.query_one("#ws-url", Input).value
        if not url:
            self.notify("URL required.", severity="error")
            return

        # Ensure scheme
        if not url.startswith("ws://") and not url.startswith("wss://"):
            url = "ws://" + url

        self.log_message(f"Connecting to {url}...", "system")
        self.query_one("#btn-ws-connect").disabled = True

        try:
            self.websocket = await websockets.connect(url)
            self.is_connected = True
            self.update_ui_connected(True)
            self.log_message("Connected!", "success")

            # Start receiver
            self.recv_task = asyncio.create_task(self.receive_loop())

        except Exception as e:
            self.log_message(f"Connection failed: {e}", "error")
            self.update_ui_connected(False)
            self.query_one("#btn-ws-connect").disabled = False

    async def disconnect(self) -> None:
        if self.websocket:
            await self.websocket.close()
            self.websocket = None

        if self.recv_task:
            self.recv_task.cancel()
            try:
                await self.recv_task
            except asyncio.CancelledError:
                pass
            self.recv_task = None

        self.is_connected = False
        self.update_ui_connected(False)
        self.log_message("Disconnected.", "system")

    async def receive_loop(self) -> None:
        if not self.websocket:
            return

        try:
            async for message in self.websocket:
                self.log_message(f"Rx: {message}", "rx")
        except websockets.ConnectionClosed:
            self.log_message("Connection closed by server.", "warning")
            self.is_connected = False
            self.update_ui_connected(False)
        except Exception as e:
            self.log_message(f"Receive error: {e}", "error")

    async def send_message(self) -> None:
        if not self.websocket or not self.is_connected:
            self.notify("Not connected.", severity="error")
            return

        inp = self.query_one("#ws-input-msg", Input)
        message = inp.value
        if not message:
            return

        try:
            await self.websocket.send(message)
            self.log_message(f"Tx: {message}", "tx")
            inp.value = ""
        except Exception as e:
            self.log_message(f"Send error: {e}", "error")
            # Usually implies connection issue
            await self.disconnect()

    def update_ui_connected(self, connected: bool) -> None:
        self.query_one("#btn-ws-connect").disabled = connected
        self.query_one("#btn-ws-disconnect").disabled = not connected
        self.query_one("#btn-ws-send").disabled = not connected

        lbl = self.query_one("#lbl-ws-status", Label)
        if connected:
            lbl.update("Connected")
            lbl.remove_class("status-disconnected")
            lbl.add_class("status-connected")
        else:
            lbl.update("Disconnected")
            lbl.remove_class("status-connected")
            lbl.add_class("status-disconnected")

    def log_message(self, message: str, type: str = "info") -> None:
        log = self.query_one("#ws-log", RichLog)
        timestamp = datetime.now().strftime("%H:%M:%S")

        color = "white"
        if type == "tx":
            color = "blue"
        elif type == "rx":
            color = "green"
        elif type == "error":
            color = "red"
        elif type == "warning":
            color = "yellow"
        elif type == "success":
            color = "green"
        elif type == "system":
            color = "dim white"

        prefix = ""
        if type == "tx":
            prefix = ">> "
        elif type == "rx":
            prefix = "<< "

        log.write(f"[{timestamp}] [{color}]{prefix}{message}[/{color}]")

        if self.query_one("#chk-ws-autoscroll", Checkbox).value:
            log.scroll_end(animate=False)
