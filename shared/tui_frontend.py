from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Static, Button, Label, Input, DataTable, RichLog, Select
from textual.containers import Container, Horizontal, Vertical
from textual import on
from shared.frontend import FrontendVerifier

class FrontendTab(Container):
    """Tab for Frontend Verification."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.verifier = FrontendVerifier(project_dir)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Frontend Verification Lab[/bold]", classes="welcome-text")

            # Actions
            with Horizontal(classes="stat-box"):
                yield Label("URL:")
                yield Input(placeholder="http://localhost:3000", id="frontend-url")
                yield Label("Snapshot Name:")
                yield Input(placeholder="homepage", id="frontend-name")

            with Horizontal(classes="stat-box"):
                yield Button("Capture Snapshot", id="btn-snap", variant="primary")
                yield Button("Capture Baseline", id="btn-baseline", variant="warning")
                yield Button("Verify", id="btn-verify", variant="success")
                yield Button("Approve Current", id="btn-approve", variant="error")

            # Results
            with Vertical(classes="stat-box"):
                yield Label("[bold]Results[/bold]")
                yield RichLog(id="frontend-log", wrap=True, highlight=True, markup=True)

            # Baselines List
            with Vertical(classes="stat-box"):
                yield Label("[bold]Baselines[/bold]")
                yield Button("Refresh List", id="btn-refresh-list", variant="default")
                yield DataTable(id="frontend-table")

    def on_mount(self) -> None:
        table = self.query_one("#frontend-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Name", "Baseline", "Current", "Diff Status")
        self.refresh_list()

    @on(Button.Pressed, "#btn-refresh-list")
    def refresh_list(self) -> None:
        table = self.query_one("#frontend-table", DataTable)
        table.clear()

        baselines = self.verifier.list_baselines()
        for b in baselines:
            # We can check if current/diff exists
            paths = self.verifier._get_paths(b)
            has_current = "Yes" if paths["current"].exists() else "No"
            has_diff = "Yes" if paths["diff"].exists() else "No"

            table.add_row(b, "Yes", has_current, has_diff)

    @on(DataTable.RowSelected, "#frontend-table")
    def on_row_selected(self, event: DataTable.RowSelected) -> None:
        # Populate name input with selected row
        # Get the row using the row key from the event
        row_key = event.row_key
        row = self.query_one("#frontend-table", DataTable).get_row(row_key)
        name = row[0]
        self.query_one("#frontend-name", Input).value = name

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-refresh-list":
            self.refresh_list()
        elif event.button.id in ["btn-snap", "btn-baseline", "btn-verify", "btn-approve"]:
            await self.handle_action(event.button.id)

    async def handle_action(self, btn_id: str) -> None:
        url = self.query_one("#frontend-url", Input).value
        name = self.query_one("#frontend-name", Input).value
        log = self.query_one("#frontend-log", RichLog)

        if not name:
            self.notify("Name required.", severity="error")
            return

        import asyncio

        if btn_id == "btn-snap":
            if not url:
                self.notify("URL required.", severity="error")
                return

            log.write(f"Capturing [bold]{name}[/bold] from {url}...")
            path = await asyncio.to_thread(self.verifier.capture_snapshot, url, name, is_baseline=False)
            if path:
                log.write(f"[green]Captured:[/green] {path.name}")
                self.notify("Snapshot captured.")
            else:
                log.write("[red]Capture failed.[/red]")
                self.notify("Capture failed.", severity="error")

        elif btn_id == "btn-baseline":
            if not url:
                self.notify("URL required.", severity="error")
                return

            log.write(f"Capturing BASELINE [bold]{name}[/bold] from {url}...")
            path = await asyncio.to_thread(self.verifier.capture_snapshot, url, name, is_baseline=True)
            if path:
                log.write(f"[green]Baseline Saved:[/green] {path.name}")
                self.notify("Baseline saved.")
            else:
                log.write("[red]Capture failed.[/red]")
                self.notify("Capture failed.", severity="error")

        elif btn_id == "btn-verify":
            log.write(f"Verifying [bold]{name}[/bold]...")
            result = await asyncio.to_thread(self.verifier.verify, name)

            if result["success"]:
                if result["match"]:
                    log.write(f"[bold green]PASS[/bold green] (Diff: {result['diff_score']:.4f})")
                    self.notify("Verification Passed.")
                else:
                    log.write(f"[bold red]FAIL[/bold red] (Diff: {result['diff_score']:.4f})")
                    log.write(f"Diff image: {result['diff_path'].name}")
                    self.notify("Verification Failed.", severity="error")
            else:
                log.write(f"[red]Error:[/red] {result.get('error')}")
                self.notify("Error during verification.", severity="error")

        elif btn_id == "btn-approve":
            if self.verifier.approve_current(name):
                log.write(f"Approved [bold]{name}[/bold]. Current is now Baseline.")
                self.notify("Snapshot approved.")
            else:
                log.write("[red]Failed to approve (no current snapshot).[/red]")
                self.notify("Approval failed.", severity="error")

        self.refresh_list()
