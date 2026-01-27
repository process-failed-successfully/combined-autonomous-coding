from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Label, Button, RichLog, Checkbox, Switch
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual import on

from shared.sentinel import Sentinel

class SentinelTab(Container):
    """Tab for the Autonomous Sentinel (Dev Guardian)."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.sentinel = None
        self.sentinel_running = False

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Sentinel Guardian[/bold]", classes="welcome-text")

            # Configuration
            with Horizontal(classes="stat-box"):
                with Vertical(id="sentinel-config-checks"):
                    yield Label("Active Checks:")
                    yield Checkbox("Lint", id="chk-lint", value=True)
                    yield Checkbox("Test", id="chk-test", value=True)
                    yield Checkbox("Type", id="chk-type", value=False)
                    yield Checkbox("Security", id="chk-security", value=False)

                with Vertical(id="sentinel-config-action"):
                    yield Label("Auto-Fix:")
                    yield Switch(value=False, id="sw-autofix")
                    yield Label("(Use with caution)", classes="dim")

                with Vertical(id="sentinel-controls"):
                    yield Button("Start Sentinel", id="btn-sentinel-toggle", variant="success")
                    yield Label("Status: Stopped", id="lbl-sentinel-status")

            # Output
            yield Label("[bold]Activity Log[/bold]")
            yield RichLog(id="sentinel-log", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        self.log_message("[dim]Sentinel ready. Configure and start.[/dim]")

    def log_message(self, message: str) -> None:
        # Check if the widget is still mounted
        try:
            log_view = self.query_one("#sentinel-log", RichLog)
            # Schedule write to be thread-safe if called from Sentinel thread
            # Use app.call_from_thread for thread safety
            if self.app:
                self.app.call_from_thread(log_view.write, message)
        except Exception:
            pass

    @on(Button.Pressed, "#btn-sentinel-toggle")
    def on_toggle(self) -> None:
        if self.sentinel_running:
            self.stop_sentinel()
        else:
            self.start_sentinel()

    def start_sentinel(self) -> None:
        checks = []
        if self.query_one("#chk-lint", Checkbox).value: checks.append("lint")
        if self.query_one("#chk-test", Checkbox).value: checks.append("test")
        if self.query_one("#chk-type", Checkbox).value: checks.append("type")
        if self.query_one("#chk-security", Checkbox).value: checks.append("security")

        if not checks:
            self.notify("Select at least one check.", severity="error")
            return

        auto_fix = self.query_one("#sw-autofix", Switch).value

        self.sentinel = Sentinel(
            self.project_dir,
            checks=checks,
            auto_fix=auto_fix,
            agent_type="gemini", # Could make this selectable
            on_log=self.log_message
        )

        try:
            self.sentinel.start(blocking=False)
            self.sentinel_running = True

            btn = self.query_one("#btn-sentinel-toggle", Button)
            btn.label = "Stop Sentinel"
            btn.variant = "error"

            lbl = self.query_one("#lbl-sentinel-status", Label)
            lbl.update("[bold green]Status: Running[/bold green]")

            self.disable_controls(True)
            self.notify("Sentinel started.")

        except Exception as e:
            self.log_message(f"[bold red]Error starting Sentinel:[/bold red] {e}")
            self.notify("Failed to start.", severity="error")

    def stop_sentinel(self, update_ui: bool = True) -> None:
        if self.sentinel:
            self.sentinel.stop()
            self.sentinel = None

        self.sentinel_running = False

        if update_ui:
            btn = self.query_one("#btn-sentinel-toggle", Button)
            btn.label = "Start Sentinel"
            btn.variant = "success"

            lbl = self.query_one("#lbl-sentinel-status", Label)
            lbl.update("Status: Stopped")

            self.disable_controls(False)
            self.log_message("[bold yellow]Sentinel stopped.[/bold yellow]")
            self.notify("Sentinel stopped.")

    def disable_controls(self, disabled: bool) -> None:
        for cid in ["#chk-lint", "#chk-test", "#chk-type", "#chk-security", "#sw-autofix"]:
            try:
                self.query_one(cid).disabled = disabled
            except Exception:
                pass

    def on_unmount(self) -> None:
        if self.sentinel_running:
            self.stop_sentinel(update_ui=False)
