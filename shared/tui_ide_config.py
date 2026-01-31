import json
from pathlib import Path
import io
import contextlib
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, Button, Checkbox, TabbedContent, TabPane, RichLog
from textual import on
from rich.syntax import Syntax

from shared.ide_config import IdeConfigManager

class IdeConfigTab(Container):
    """Tab for generating IDE configurations."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = IdeConfigManager(project_dir)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]IDE Configuration Generator[/bold]", classes="welcome-text")

            # Status
            with Horizontal(classes="stat-box"):
                yield Label("Detected Project Type: ", id="lbl-ide-project-type")
                yield Label("...", id="val-ide-project-type", classes="value")
                yield Button("Refresh", id="btn-ide-refresh", variant="default")

            # Preview
            with TabbedContent(id="ide-preview-tabs"):
                with TabPane("settings.json", id="tab-ide-settings"):
                    yield RichLog(id="log-ide-settings", wrap=True, highlight=True, markup=True)
                with TabPane("launch.json", id="tab-ide-launch"):
                    yield RichLog(id="log-ide-launch", wrap=True, highlight=True, markup=True)
                with TabPane("extensions.json", id="tab-ide-extensions"):
                    yield RichLog(id="log-ide-extensions", wrap=True, highlight=True, markup=True)

            # Actions
            with Horizontal(classes="stat-box"):
                yield Checkbox("Force Overwrite", id="chk-ide-force")
                yield Button("Generate Configuration", id="btn-ide-generate", variant="primary")

            # Output Log
            yield Label("[bold]Output Log[/bold]")
            yield RichLog(id="log-ide-output", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        self.refresh_preview()

    @on(Button.Pressed, "#btn-ide-refresh")
    def on_refresh(self) -> None:
        self.refresh_preview()
        self.notify("Preview refreshed.")

    @on(Button.Pressed, "#btn-ide-generate")
    def on_generate(self) -> None:
        self.generate_config()

    def refresh_preview(self) -> None:
        project_type = self.manager.detect_project_type()
        self.query_one("#val-ide-project-type", Label).update(f"[bold cyan]{project_type}[/bold cyan]")

        previews = self.manager.get_config_previews()

        self._update_log("log-ide-settings", previews.get("settings.json"))
        self._update_log("log-ide-launch", previews.get("launch.json"))
        self._update_log("log-ide-extensions", previews.get("extensions.json"))

    def _update_log(self, log_id: str, content: dict | None) -> None:
        log = self.query_one(f"#{log_id}", RichLog)
        log.clear()
        if content:
            json_str = json.dumps(content, indent=4)
            log.write(Syntax(json_str, "json", theme="monokai"))
        else:
            log.write("No content generated.")

    def generate_config(self) -> None:
        force = self.query_one("#chk-ide-force", Checkbox).value
        output_log = self.query_one("#log-ide-output", RichLog)
        output_log.clear()
        output_log.write("Generating configuration...")

        # Capture stdout
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            success = self.manager.generate_vscode_config(force=force)

        output = f.getvalue()
        output_log.write(output)

        if success:
            self.notify("Configuration generated successfully.")
            output_log.write("\n[bold green]Success![/bold green]")
        else:
            self.notify("Failed to generate configuration.", severity="error")
            output_log.write("\n[bold red]Failed.[/bold red]")
