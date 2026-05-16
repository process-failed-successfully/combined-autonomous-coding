from pathlib import Path
from textual.app import ComposeResult
from textual.containers import VerticalScroll, Horizontal
from textual.widgets import Input, Button, Label, Static
from textual import on

from shared.favicon_lab import FaviconManager

class FaviconLabTab(VerticalScroll):
    """TUI tab for the Favicon Lab."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        yield Label("Favicon Generator", classes="header-label")
        yield Label("Source Image (must be at least 512x512):")
        yield Input(placeholder="e.g., logo.png", id="favicon-image-input")
        yield Label("Output Directory:")
        yield Input(value=".", placeholder="e.g., public", id="favicon-output-input")
        with Horizontal(id="favicon-buttons"):
            yield Button("Generate Favicons", id="favicon-generate-btn", variant="primary")
            yield Button("Show HTML Tags", id="favicon-html-btn")
        yield Static("", id="favicon-output", classes="output-panel")

    @on(Button.Pressed, "#favicon-generate-btn")
    def generate_favicons(self) -> None:
        image_input = self.query_one("#favicon-image-input", Input)
        output_input = self.query_one("#favicon-output-input", Input)
        output_panel = self.query_one("#favicon-output", Static)

        image_path = image_input.value.strip()
        out_dir = output_input.value.strip()

        if not image_path:
            output_panel.update("Error: Source image path is required.")
            return

        manager = FaviconManager(self.project_dir)

        img_full_path = self.project_dir / image_path
        if not img_full_path.exists():
            output_panel.update(f"Error: Source image '{image_path}' not found.")
            return

        success = manager.generate(image_path, out_dir)
        if success:
            output_panel.update("✅ Generated favicons successfully!\n- favicon.ico\n- apple-touch-icon.png\n- site.webmanifest")
        else:
            output_panel.update("❌ Failed to generate favicons. Ensure the image is valid and at least 512x512.")

    @on(Button.Pressed, "#favicon-html-btn")
    def show_html(self) -> None:
        output_panel = self.query_one("#favicon-output", Static)
        manager = FaviconManager(self.project_dir)
        html_code = manager.html()
        output_panel.update(f"```html\n{html_code}\n```")
