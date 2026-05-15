from textual.app import ComposeResult
from textual.containers import VerticalScroll, Horizontal, Vertical
from textual.widgets import Label, Input, Button, Static, Markdown
from textual import on
from shared.favicon_lab import FaviconManager
from pathlib import Path

class FaviconLabTab(VerticalScroll):
    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = FaviconManager()

    def compose(self) -> ComposeResult:
        if not self.manager.pillow_available:
            yield Label("Pillow is required for Favicon Lab. Please install it with 'pip install Pillow'", id="favicon-warning")
            return

        yield Markdown("# Favicon Lab", id="favicon-title")

        with Vertical(id="favicon-generate-section", classes="section"):
            yield Label("Source Image Path:")
            yield Input(placeholder="e.g. logo.png", id="favicon-input-path")
            yield Label("Output Directory:")
            yield Input(value=str(self.project_dir), id="favicon-output-dir")
            yield Button("Generate Favicons", id="favicon-generate-btn", variant="primary")
            yield Static("", id="favicon-generate-result")

        with Vertical(id="favicon-html-section", classes="section"):
            yield Markdown("### HTML Snippet")
            yield Static(self.manager.get_html(), id="favicon-html-output")

    @on(Button.Pressed, "#favicon-generate-btn")
    def generate_favicons(self, event: Button.Pressed) -> None:
        input_path = self.query_one("#favicon-input-path", Input).value
        output_dir = self.query_one("#favicon-output-dir", Input).value
        result_display = self.query_one("#favicon-generate-result", Static)

        if not input_path:
            result_display.update("[red]Input path is required.[/red]")
            return

        success, msg = self.manager.generate(input_path, output_dir)
        if success:
            result_display.update(f"[green]{msg}[/green]")
        else:
            result_display.update(f"[red]{msg}[/red]")
