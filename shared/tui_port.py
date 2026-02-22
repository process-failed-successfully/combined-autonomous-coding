from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, DataTable, Input, Label

from shared.port_manager import PortManager


class PortLabTab(Container):
    """Tab for managing listening ports and processes."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.ports_cache = []
        self.selected_port = None

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Port Manager[/bold]", classes="welcome-text")

            with Horizontal(classes="stat-box"):
                yield Button("Refresh", id="btn-refresh-ports", variant="primary")
                yield Button("Kill Process", id="btn-kill-port", variant="error", disabled=True)
                yield Input(placeholder="Filter by process name...", id="input-port-filter")

            yield DataTable(id="port-table")

    def on_mount(self) -> None:
        table = self.query_one("#port-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Port", "PID", "Process Name", "User")
        self.load_ports()

    def load_ports(self) -> None:
        table = self.query_one("#port-table", DataTable)
        table.clear()

        # Reset selection state
        self.selected_port = None
        self.query_one("#btn-kill-port").disabled = True

        try:
            self.ports_cache = PortManager.list_listening_ports()
            self._update_table()
            self.notify(f"Loaded {len(self.ports_cache)} ports.")
        except Exception as e:
            self.notify(f"Error loading ports: {e}", severity="error")

    def _update_table(self) -> None:
        table = self.query_one("#port-table", DataTable)
        table.clear()

        filter_text = self.query_one("#input-port-filter", Input).value.lower()

        for port_info in self.ports_cache:
            name = port_info.get("name", "unknown")
            if filter_text and filter_text not in name.lower():
                continue

            port = str(port_info["port"])
            pid = str(port_info.get("pid") or "?")
            user = port_info.get("username", "unknown")

            # Use port as key
            table.add_row(port, pid, name, user, key=port)

    @on(Button.Pressed, "#btn-refresh-ports")
    def on_refresh(self) -> None:
        self.load_ports()

    @on(Button.Pressed, "#btn-kill-port")
    def on_kill(self) -> None:
        if not self.selected_port:
            return

        try:
            port = int(self.selected_port)
            success = PortManager.kill_process_on_port(port)
            if success:
                self.notify(f"Process on port {port} killed.")
                self.load_ports()
            else:
                self.notify(f"Failed to kill process on port {port}.", severity="error")
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    @on(DataTable.RowSelected, "#port-table")
    def on_row_selected(self, event: DataTable.RowSelected) -> None:
        self.selected_port = event.row_key.value
        self.query_one("#btn-kill-port").disabled = False

    @on(Input.Changed, "#input-port-filter")
    def on_filter_changed(self) -> None:
        self._update_table()
