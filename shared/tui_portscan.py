import asyncio
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Input, Button, DataTable, Label, RichLog, Static
from textual.reactive import reactive
from shared.portscan_lab import PortScanManager, parse_port_range

class PortScanTab(Vertical):
    """TUI Tab for PortScan Lab."""

    is_scanning = reactive(False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.manager = PortScanManager()
        self.scan_task = None
        self._current_host = ""
        self._current_ports = ""

    def compose(self) -> ComposeResult:
        yield Label("PortScan Lab", classes="tab-title")
        yield Label("Scan open ports on a host efficiently.", classes="tab-description")

        with Horizontal(id="portscan-inputs-container"):
            yield Input(placeholder="Host (e.g., example.com, 127.0.0.1)", id="portscan-host", value="127.0.0.1")
            yield Input(placeholder="Ports (e.g., 80, 1-1024)", id="portscan-ports", value="1-1024")
            yield Button("Scan", id="btn-portscan", variant="primary")
            yield Button("Cancel", id="btn-portscan-cancel", variant="error", disabled=True)

        with Horizontal(id="portscan-options-container"):
            yield Label("Timeout (s):", classes="portscan-option-label")
            yield Input(value="1.0", id="portscan-timeout", classes="portscan-option-input")
            yield Label("Concurrency:", classes="portscan-option-label")
            yield Input(value="100", id="portscan-concurrency", classes="portscan-option-input")

        yield Label("", id="portscan-status")

        yield DataTable(id="portscan-table")

    def on_mount(self) -> None:
        table = self.query_one("#portscan-table", DataTable)
        table.add_columns("Port", "Service")

    def watch_is_scanning(self, is_scanning: bool) -> None:
        """Update UI based on scanning state."""
        self.query_one("#btn-portscan", Button).disabled = is_scanning
        self.query_one("#btn-portscan-cancel", Button).disabled = not is_scanning
        self.query_one("#portscan-host", Input).disabled = is_scanning
        self.query_one("#portscan-ports", Input).disabled = is_scanning
        self.query_one("#portscan-timeout", Input).disabled = is_scanning
        self.query_one("#portscan-concurrency", Input).disabled = is_scanning

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-portscan":
            await self.start_scan()
        elif event.button.id == "btn-portscan-cancel":
            self.cancel_scan()

    async def start_scan(self) -> None:
        host = self.query_one("#portscan-host", Input).value.strip()
        ports_str = self.query_one("#portscan-ports", Input).value.strip()

        if not host or not ports_str:
            self.notify("Please enter host and ports.", title="Error", severity="error")
            return

        try:
            start_port, end_port = parse_port_range(ports_str)
        except ValueError as e:
            self.notify(str(e), title="Error", severity="error")
            return

        try:
            timeout = float(self.query_one("#portscan-timeout", Input).value.strip())
            concurrency = int(self.query_one("#portscan-concurrency", Input).value.strip())
        except ValueError:
            self.notify("Invalid timeout or concurrency.", title="Error", severity="error")
            return

        self._current_host = host
        self._current_ports = ports_str
        self.is_scanning = True

        table = self.query_one("#portscan-table", DataTable)
        table.clear()

        status_lbl = self.query_one("#portscan-status", Label)
        status_lbl.update(f"Scanning {host} ports {start_port}-{end_port}...")

        self.scan_task = asyncio.create_task(
            self.run_scan_async(host, start_port, end_port, timeout, concurrency)
        )

    def cancel_scan(self) -> None:
        if self.is_scanning:
            self.manager.cancel()
            status_lbl = self.query_one("#portscan-status", Label)
            status_lbl.update(f"Scan cancelled for {self._current_host}.")
            self.is_scanning = False
            self.notify("Scan cancelled.", title="PortScan")

    async def run_scan_async(self, host: str, start_port: int, end_port: int, timeout: float, concurrency: int):
        table = self.query_one("#portscan-table", DataTable)

        def on_port_scanned(result):
            port, is_open, service = result
            if is_open:
                self.app.call_from_thread(table.add_row, str(port), service)

        try:
            open_ports = await self.manager.scan_ports(
                host=host,
                start_port=start_port,
                end_port=end_port,
                timeout=timeout,
                concurrency=concurrency,
                callback=on_port_scanned
            )

            if self.is_scanning: # Check if not cancelled
                status_lbl = self.query_one("#portscan-status", Label)
                status_lbl.update(f"Scan complete. Found {len(open_ports)} open ports.")
                self.notify(f"Found {len(open_ports)} open ports on {host}.", title="PortScan Complete")

        except Exception as e:
            self.notify(f"Error during scan: {e}", title="Error", severity="error")
            status_lbl = self.query_one("#portscan-status", Label)
            status_lbl.update("Scan failed.")
        finally:
            self.is_scanning = False
