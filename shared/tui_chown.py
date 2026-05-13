from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Label, Input, Button, DataTable
from textual import on

try:
    from shared.chown_lab import ChownManager
except ImportError:
    # Handle missing dependency gracefully in testing
    ChownManager = None

from textual.widget import Widget

class ChownLabTab(Vertical):
    """Tab for Unix Ownership (Chown) Lab."""

    DEFAULT_CSS = """
    ChownLabTab {
        padding: 1;
        overflow: auto;
    }

    .welcome-text {
        text-align: center;
        width: 100%;
        margin-bottom: 1;
        text-style: bold;
        color: $accent;
    }

    .stat-box {
        border: solid $accent;
        padding: 1;
        margin-top: 1;
        height: auto;
    }

    .result-label {
        width: 15;
        text-align: right;
        padding-right: 1;
    }

    #chown-table-container {
        height: 15;
        margin-top: 1;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = ChownManager() if ChownManager else None
        self.updating_ui = False

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Chown Lab (Ownership Tool)[/bold]", classes="welcome-text")

            # File Operations
            with Vertical(classes="stat-box"):
                yield Label("[bold]File Ownership Operations[/bold]")
                with Horizontal():
                    yield Label("Path:", classes="result-label")
                    yield Input(placeholder="/path/to/file", id="input-chown-path")

                with Horizontal():
                    yield Button("Load Ownership", id="btn-chown-load", variant="primary")
                    yield Button("Apply Ownership", id="btn-chown-apply", variant="error")

                yield Label("", id="lbl-chown-status")

                with Horizontal(classes="stat-box"):
                    with Vertical():
                        yield Label("Current Ownership:")
                        yield Input(value="", id="input-chown-current", disabled=True)
                    with Vertical():
                        yield Label("New Ownership (user:group):")
                        yield Input(value="", id="input-chown-new", placeholder="e.g. root:root")

            # Listing
            with Vertical(classes="stat-box"):
                yield Label("[bold]System Users & Groups[/bold]")
                with Horizontal():
                    yield Button("List Users", id="btn-chown-list-users")
                    yield Button("List Groups", id="btn-chown-list-groups")

                with Vertical(id="chown-table-container"):
                    yield DataTable(id="dt-chown-list")

    @on(Button.Pressed, "#btn-chown-load")
    def on_load_file(self) -> None:
        if not self.manager:
            return
        path = self.query_one("#input-chown-path", Input).value
        if not path:
            self.notify("Path is empty.", severity="warning")
            return

        res = self.manager.get_ownership(path)
        status_lbl = self.query_one("#lbl-chown-status", Label)

        if "error" in res:
            status_lbl.update(f"[red]Error: {res['error']}[/red]")
            self.notify("Failed to load ownership.", severity="error")
        else:
            ownership = res["formatted"]
            self.query_one("#input-chown-current", Input).value = ownership
            self.query_one("#input-chown-new", Input).value = ownership
            status_lbl.update(f"[green]Loaded ownership: {ownership}[/green]")
            self.notify("Ownership loaded.")

    @on(Button.Pressed, "#btn-chown-apply")
    def on_apply_file(self) -> None:
        if not self.manager:
            return
        path = self.query_one("#input-chown-path", Input).value
        ownership = self.query_one("#input-chown-new", Input).value

        if not path or not ownership:
            self.notify("Path or Ownership value is empty.", severity="error")
            return

        status_lbl = self.query_one("#lbl-chown-status", Label)

        if self.manager.set_ownership(path, ownership):
            status_lbl.update(f"[green]Applied {ownership} to {path}[/green]")
            self.notify(f"Ownership set to {ownership}.")
        else:
            status_lbl.update(f"[red]Failed to set ownership.[/red]")
            self.notify("Failed to set ownership.", severity="error")

    @on(Button.Pressed, "#btn-chown-list-users")
    def on_list_users(self) -> None:
        if not self.manager:
            return
        users = self.manager.list_users()
        dt = self.query_one("#dt-chown-list", DataTable)
        dt.clear(columns=True)
        dt.add_columns("UID", "User", "Home", "Shell")

        for u in users:
            dt.add_row(str(u["uid"]), u["user"], u["dir"], u["shell"])

    @on(Button.Pressed, "#btn-chown-list-groups")
    def on_list_groups(self) -> None:
        if not self.manager:
            return
        groups = self.manager.list_groups()
        dt = self.query_one("#dt-chown-list", DataTable)
        dt.clear(columns=True)
        dt.add_columns("GID", "Group", "Members")

        for g in groups:
            members = ",".join(g["members"])
            dt.add_row(str(g["gid"]), g["group"], members)
