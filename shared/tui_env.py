from textual.app import ComposeResult
from textual.widgets import Label, Button, DataTable, Input, RichLog
from textual.containers import Container, Vertical, Horizontal
from textual import on
from shared.env_manager import EnvManager
from pathlib import Path

class EnvTab(Container):
    """Tab for managing environment variables (.env)."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = EnvManager(project_dir)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Environment Variables[/bold]", classes="welcome-text")

            # Status Header
            with Horizontal(classes="stat-box", id="env-status-container"):
                yield Label("Status: Loading...", id="lbl-env-status")
                yield Button("Check/Refresh", id="btn-env-check", variant="default")

            # Comparison Table
            yield DataTable(id="env-table")

            # Actions
            with Horizontal(classes="stat-box", id="env-actions-container"):
                yield Button("Init Files", id="btn-env-init", variant="warning", disabled=True)
                yield Button("Sync Keys", id="btn-env-sync", variant="primary", disabled=True)

            # Secret Generator
            with Horizontal(classes="stat-box", id="env-secret-container"):
                yield Label("Generate Secret for Key:")
                yield Input(placeholder="KEY_NAME...", id="inp-env-key")
                yield Button("Generate", id="btn-env-generate", variant="success")

            # Log/Output
            yield RichLog(id="env-log", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        table = self.query_one("#env-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Key", ".env", ".env.example")
        self.refresh_status()

    def refresh_status(self) -> None:
        is_valid, missing_env, missing_example = self.manager.check()

        # Determine status text
        lbl = self.query_one("#lbl-env-status", Label)
        init_btn = self.query_one("#btn-env-init", Button)
        sync_btn = self.query_one("#btn-env-sync", Button)

        if not self.manager.env_path.exists() and not self.manager.example_path.exists():
            lbl.update("[red]Files missing[/red]")
            init_btn.disabled = False
            sync_btn.disabled = True
        elif is_valid:
            lbl.update("[green]Synced[/green]")
            init_btn.disabled = True
            sync_btn.disabled = True
        else:
            lbl.update("[yellow]Out of Sync[/yellow]")
            init_btn.disabled = True
            sync_btn.disabled = False

        self.populate_table()

    def populate_table(self) -> None:
        table = self.query_one("#env-table", DataTable)
        table.clear()

        # We access _parse_env directly to get keys.
        # This is a pragmatic choice for the TUI to avoid re-implementing parsing.
        env_vars = self.manager._parse_env(self.manager.env_path)
        example_vars = self.manager._parse_env(self.manager.example_path)

        all_keys = sorted(set(list(env_vars.keys()) + list(example_vars.keys())))

        for key in all_keys:
            in_env = "[green]Present[/green]" if key in env_vars else "[red]Missing[/red]"
            in_example = "[green]Present[/green]" if key in example_vars else "[red]Missing[/red]"

            # Highlight mismatch
            if (key in env_vars) != (key in example_vars):
                key_display = f"[bold yellow]{key}[/bold yellow]"
            else:
                key_display = key

            table.add_row(key_display, in_env, in_example)

    @on(Button.Pressed, "#btn-env-check")
    def on_check(self) -> None:
        self.refresh_status()
        self.notify("Environment status refreshed.")

    @on(Button.Pressed, "#btn-env-init")
    def on_init(self) -> None:
        success, msg = self.manager.init()
        log = self.query_one("#env-log", RichLog)
        if success:
            log.write(f"[green]{msg}[/green]")
            self.notify("Initialized.")
        else:
            log.write(f"[yellow]{msg}[/yellow]")
        self.refresh_status()

    @on(Button.Pressed, "#btn-env-sync")
    def on_sync(self) -> None:
        # Sync non-interactively for now
        success, msg = self.manager.sync(interactive=False)
        log = self.query_one("#env-log", RichLog)
        if success:
            log.write(f"[green]{msg}[/green]")
            self.notify("Synced.")
        else:
            log.write(f"[red]{msg}[/red]")
            self.notify("Sync failed.", severity="error")
        self.refresh_status()

    @on(Button.Pressed, "#btn-env-generate")
    def on_generate(self) -> None:
        inp = self.query_one("#inp-env-key", Input)
        key = inp.value.strip()
        if not key:
            self.notify("Key name required.", severity="error")
            return

        try:
            secret = self.manager.generate_secret(key)
            log = self.query_one("#env-log", RichLog)
            log.write(f"Generated secret for [bold]{key}[/bold]")
            self.notify(f"Secret generated for {key}")
            inp.value = ""
            self.refresh_status()
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")
