from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Label, Button, Input, DataTable
from textual.containers import Container, Horizontal, Vertical
from textual import on
from shared.host_lab import HostLabManager
import sys

class HostLabTab(Container):
    """Tab for managing /etc/hosts entries."""

    def __init__(self, project_dir: Path = None, **kwargs) -> None:
        super().__init__(**kwargs)
        # Use default system path if not provided
        if sys.platform == "win32":
            default_path = Path(r"C:\Windows\System32\drivers\etc\hosts")
        else:
            default_path = Path("/etc/hosts")

        self.hosts_path = default_path
        self.manager = HostLabManager(self.hosts_path)
        self.selected_host = None

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Host Lab[/bold]", classes="welcome-text")

            # Actions
            with Horizontal(classes="stat-box"):
                yield Button("Refresh", id="btn-host-refresh", variant="default")
                yield Button("Backup Hosts", id="btn-host-backup", variant="success")

            # List
            with Vertical(classes="stat-box", id="host-list-container"):
                yield DataTable(id="host-table")
                with Horizontal():
                    yield Button("Toggle Selected", id="btn-host-toggle", variant="warning", disabled=True)
                    yield Button("Remove Selected", id="btn-host-remove", variant="error", disabled=True)

            # Add Entry
            with Vertical(classes="stat-box"):
                yield Label("[bold]Add Entry[/bold]")
                with Horizontal():
                    yield Input(placeholder="IP Address", id="input-host-ip")
                    yield Input(placeholder="Hostname", id="input-host-name")
                    yield Input(placeholder="Comment (optional)", id="input-host-comment")
                    yield Button("Add", id="btn-host-add", variant="primary")

    def on_mount(self) -> None:
        table = self.query_one("#host-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Status", "IP", "Hostname", "Comment")
        self.load_entries()

    def load_entries(self) -> None:
        table = self.query_one("#host-table", DataTable)
        table.clear()

        entries = self.manager.list_entries()

        for i, e in enumerate(entries):
            if e['type'] == 'entry':
                status = "[green]Active[/green]" if e['enabled'] else "[red]Disabled[/red]"
                ip = e['ip']
                # Join multiple hosts if any
                hosts = ", ".join(e['hosts'])
                comment = e.get('comment', "") or ""

                # Use line number as the unique key
                # key = str(e.get('line_num', i)) # Fallback to index if line_num missing (safety)
                # table.add_row(status, ip, hosts, comment, key=key)
                # Let Textual generate unique keys to avoid DuplicateKey errors
                table.add_row(status, ip, hosts, comment)

    @on(DataTable.RowSelected, "#host-table")
    def on_row_selected(self, event: DataTable.RowSelected) -> None:
        table = self.query_one("#host-table", DataTable)
        row_data = table.get_row(event.row_key)
        # Hostname is at index 2 (comma separated)
        hosts_str = row_data[2]
        # Use first host for action
        self.selected_host = hosts_str.split(",")[0].strip()

        self.query_one("#btn-host-toggle").disabled = False
        self.query_one("#btn-host-remove").disabled = False

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-host-refresh":
            self.load_entries()
            self.notify("Refreshed.")

        elif event.button.id == "btn-host-backup":
            path = self.manager.backup()
            if path:
                self.notify(f"Backup created: {path.name}")
            else:
                self.notify("Backup failed.", severity="error")

        elif event.button.id == "btn-host-add":
            ip = self.query_one("#input-host-ip", Input).value
            host = self.query_one("#input-host-name", Input).value
            comment = self.query_one("#input-host-comment", Input).value

            if not ip or not host:
                self.notify("IP and Hostname required.", severity="error")
                return

            if self.manager.add_entry(ip, host, comment):
                self.notify(f"Added {host}")
                self.query_one("#input-host-ip", Input).value = ""
                self.query_one("#input-host-name", Input).value = ""
                self.query_one("#input-host-comment", Input).value = ""
                self.load_entries()
            else:
                self.notify("Failed to add entry.", severity="error")

        elif event.button.id == "btn-host-toggle":
            if self.selected_host:
                if self.manager.toggle_entry(self.selected_host):
                    self.notify(f"Toggled {self.selected_host}")
                    self.load_entries()
                else:
                    self.notify("Failed to toggle entry.", severity="error")

        elif event.button.id == "btn-host-remove":
            if self.selected_host:
                if self.manager.remove_entry(self.selected_host):
                    self.notify(f"Removed {self.selected_host}")
                    self.selected_host = None
                    self.query_one("#btn-host-toggle").disabled = True
                    self.query_one("#btn-host-remove").disabled = True
                    self.load_entries()
                else:
                    self.notify("Failed to remove entry.", severity="error")
