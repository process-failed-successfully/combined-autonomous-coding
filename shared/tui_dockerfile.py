from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Label, Button, Input, Static, TabPane, Markdown, RichLog
from textual.containers import Container, Horizontal, Vertical
from textual import on

from shared.dockerfile_lab import DockerfileLabManager

class DockerfileLabTab(TabPane):
    """Tab for Dockerfile Lab."""

    def __init__(self, project_dir: Path, **kwargs):
        super().__init__("Dockerfile Lab", id="tab-dockerfile", **kwargs)
        self.project_dir = project_dir
        self.manager = None
        self.generated_files = {}

    def compose(self) -> ComposeResult:
        with Vertical(id="dockerfile-container", classes="lab-container"):
            yield Label("[bold]Dockerfile Lab[/bold]", classes="welcome-text")
            yield Label("Generate Docker configurations based on your project.", classes="subtitle")

            with Horizontal(id="dockerfile-config-section"):
                with Vertical(classes="section-box"):
                    yield Label("[bold]Project Configuration[/bold]")
                    with Horizontal(classes="input-group"):
                        yield Label("Project Directory:")
                        yield Input(id="dockerfile-project-dir", value=str(self.project_dir))
                    with Horizontal(classes="input-group"):
                        yield Button("Detect Project Type", id="btn-dockerfile-detect", variant="primary")
                        yield Label("", id="dockerfile-project-type-lbl", classes="status-label")

                    yield Button("Generate Configs", id="btn-dockerfile-generate", variant="success", disabled=True)
                    yield Button("Save Files", id="btn-dockerfile-save", variant="warning", disabled=True)

            with Vertical(id="dockerfile-results-section", classes="section-box"):
                yield Label("[bold]Preview[/bold]")
                yield RichLog(id="dockerfile-preview-log", wrap=False, highlight=True)

    @on(Button.Pressed, "#btn-dockerfile-detect")
    def on_detect_pressed(self) -> None:
        dir_val = self.query_one("#dockerfile-project-dir", Input).value.strip()
        if not dir_val:
            self.query_one("#dockerfile-project-type-lbl", Label).update("[red]Directory is required.[/red]")
            return

        project_dir = Path(dir_val).resolve()
        if not project_dir.exists() or not project_dir.is_dir():
            self.query_one("#dockerfile-project-type-lbl", Label).update(f"[red]Directory not found: {project_dir}[/red]")
            return

        try:
            self.manager = DockerfileLabManager(project_dir)
            if self.manager.project_type == "unknown":
                self.query_one("#dockerfile-project-type-lbl", Label).update("[red]Unknown project type.[/red]")
                self.query_one("#btn-dockerfile-generate", Button).disabled = True
            else:
                self.query_one("#dockerfile-project-type-lbl", Label).update(f"[bold green]Detected: {self.manager.project_type}[/bold green]")
                self.query_one("#btn-dockerfile-generate", Button).disabled = False
        except Exception as e:
            self.query_one("#dockerfile-project-type-lbl", Label).update(f"[red]Error: {e}[/red]")
            self.query_one("#btn-dockerfile-generate", Button).disabled = True

    @on(Button.Pressed, "#btn-dockerfile-generate")
    def on_generate_pressed(self) -> None:
        if not self.manager:
            return

        log = self.query_one("#dockerfile-preview-log", RichLog)
        log.clear()

        try:
            self.generated_files = self.manager.generate()

            for filename, content in self.generated_files.items():
                log.write(f"[bold cyan]--- {filename} ---[/bold cyan]")
                log.write(content)
                log.write("\n")

            self.query_one("#btn-dockerfile-save", Button).disabled = False
        except Exception as e:
            log.write(f"[red]Error generating configs: {e}[/red]")
            self.query_one("#btn-dockerfile-save", Button).disabled = True

    @on(Button.Pressed, "#btn-dockerfile-save")
    def on_save_pressed(self) -> None:
        if not self.manager or not self.generated_files:
            return

        log = self.query_one("#dockerfile-preview-log", RichLog)

        try:
            saved = self.manager.save_files(self.generated_files, force=True) # UI handles intent to save
            if saved:
                log.write(f"\n[bold green]✅ Saved {len(saved)} files to {self.manager.project_dir}[/bold green]")
                for f in saved:
                    log.write(f" - {f}")
            else:
                log.write("\n[yellow]No files were saved.[/yellow]")
        except Exception as e:
            log.write(f"\n[bold red]Error saving files: {e}[/bold red]")
