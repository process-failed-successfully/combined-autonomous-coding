import asyncio
from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Input, Label, RichLog, Select, Checkbox
from textual import on
from rich.text import Text

from shared.sock_lab import SockLabManager

class SockLabTab(Container):
    """Tab for Socket Lab (Netcat-like)."""

    def __init__(self, project_dir: Path = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = SockLabManager()
        self.is_connected = False

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Socket Lab[/bold]", classes="welcome-text")

            # Connection Controls
            with Horizontal(classes="stat-box"):
                yield Select.from_values(["Client", "Server"], id="sock-mode", value="Client")
                yield Label("Host:", classes="label")
                yield Input(placeholder="e.g. localhost", value="localhost", id="sock-host")
                yield Label("Port:", classes="label")
                yield Input(placeholder="e.g. 8080", value="8080", id="sock-port", type="integer")
                yield Button("Connect", id="btn-sock-connect", variant="primary")
                yield Button("Disconnect", id="btn-sock-disconnect", variant="error", disabled=True)

            # Output
            with VerticalScroll(id="sock-output-container", classes="stat-box"):
                yield Label("[bold]Output[/bold]")
                yield RichLog(id="sock-log", wrap=True, highlight=False, markup=True)

            # Input
            with Horizontal(classes="stat-box"):
                yield Input(placeholder="Type message...", id="sock-input", disabled=True)
                yield Button("Send", id="btn-sock-send", variant="success", disabled=True)
                yield Checkbox("Hex View", id="chk-sock-hex", value=False)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-sock-connect":
            await self.connect()
        elif event.button.id == "btn-sock-disconnect":
            self.disconnect()
        elif event.button.id == "btn-sock-send":
            await self.send_message()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "sock-input":
            await self.send_message()

    async def connect(self) -> None:
        mode = self.query_one("#sock-mode", Select).value
        host = self.query_one("#sock-host", Input).value
        port_str = self.query_one("#sock-port", Input).value

        if not host or not port_str:
            self.notify("Host and Port required.", severity="error")
            return

        try:
            port = int(port_str)
        except ValueError:
            self.notify("Invalid port.", severity="error")
            return

        self.query_one("#btn-sock-connect").disabled = True
        self.query_one("#sock-mode").disabled = True
        self.query_one("#sock-host").disabled = True
        self.query_one("#sock-port").disabled = True
        self.query_one("#sock-log", RichLog).clear()

        self.notify(f"Starting {mode} on {host}:{port}...")

        # Reset manager
        self.manager = SockLabManager()

        # Callbacks
        def on_data(data: bytes):
            self.app.call_from_thread(self.append_log, data, "remote")

        def on_error(msg: str):
            self.app.call_from_thread(self.log_error, msg)
            self.app.call_from_thread(self.on_disconnect)

        def on_connect_client():
            self.app.call_from_thread(self.log_info, f"Connected to {host}:{port}")
            self.app.call_from_thread(self.set_connected, True)

        def on_connect_server(addr: str):
            self.app.call_from_thread(self.log_info, f"Accepted connection from {addr}")
            self.app.call_from_thread(self.set_connected, True)

        import asyncio
        if mode == "Client":
            asyncio.create_task(self.manager.start_client(host, port, on_data, on_error, on_connect_client))
        else:
            self.log_info(f"Listening on {host}:{port}...")
            asyncio.create_task(self.manager.start_server(host, port, on_data, on_error, on_connect_server))

    def disconnect(self) -> None:
        self.manager.stop()
        self.on_disconnect()

    def on_disconnect(self) -> None:
        self.set_connected(False)
        self.log_info("Disconnected.")

        self.query_one("#btn-sock-connect").disabled = False
        self.query_one("#sock-mode").disabled = False
        self.query_one("#sock-host").disabled = False
        self.query_one("#sock-port").disabled = False

    def set_connected(self, connected: bool) -> None:
        self.is_connected = connected
        self.query_one("#btn-sock-disconnect").disabled = not connected
        self.query_one("#btn-sock-send").disabled = not connected
        self.query_one("#sock-input").disabled = not connected

        if connected:
            self.query_one("#sock-input").focus()

    async def send_message(self) -> None:
        if not self.is_connected:
            return

        inp = self.query_one("#sock-input", Input)
        text = inp.value
        if not text:
            return

        # Send data (with newline)
        data = f"{text}\n".encode()
        await self.manager.send_data(data)

        self.append_log(data, "local")
        inp.value = ""

    def append_log(self, data: bytes, source: str) -> None:
        log = self.query_one("#sock-log", RichLog)

        hex_view = self.query_one("#chk-sock-hex", Checkbox).value

        if source == "local":
            style = "bold blue"
            prefix = ">>> "
        else:
            style = "bold green"
            prefix = "<<< "

        if hex_view:
            # Hex dump
            hex_str = " ".join(f"{b:02x}" for b in data)
            log.write(Text(f"{prefix}{hex_str}", style=style))
        else:
            # Text view (decode safely)
            text = data.decode('utf-8', errors='replace').rstrip()
            log.write(Text(f"{prefix}{text}", style=style))

    def log_info(self, msg: str) -> None:
        self.query_one("#sock-log", RichLog).write(f"[yellow]{msg}[/yellow]")

    def log_error(self, msg: str) -> None:
        self.query_one("#sock-log", RichLog).write(f"[bold red]{msg}[/bold red]")
