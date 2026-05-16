import os
from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.widgets import Header, Footer, Button, Label, Input, Static, TabPane
from textual import work

class FaviconLabTab(TabPane):
    """A tab for generating Favicons from an image."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        self.project_dir = project_dir
        super().__init__("Favicon Lab", **kwargs)

    def compose(self) -> ComposeResult:
        with Vertical(id="favicon-container"):
            yield Label("Favicon Generator", classes="header-label")
            yield Label("Source Image Path:")
            yield Input(placeholder="e.g. logo.png", id="favicon-source")
            yield Label("Output Directory:")
            yield Input(placeholder="e.g. public/", id="favicon-output")
            yield Label("App Name:")
            yield Input(value="My App", id="favicon-app-name")

            with Horizontal(classes="buttons"):
                yield Button("Generate Favicons", id="btn-generate-favicons", variant="primary")
                yield Button("Show HTML Tags", id="btn-show-html", variant="default")

            yield Label("Result:", classes="section-label")
            yield Static("", id="favicon-result", classes="result-box")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-generate-favicons":
            source = self.query_one("#favicon-source", Input).value
            output = self.query_one("#favicon-output", Input).value
            app_name = self.query_one("#favicon-app-name", Input).value

            if not source or not output:
                self.query_one("#favicon-result", Static).update("Error: Source and Output paths are required.")
                return

            self.query_one("#favicon-result", Static).update("Generating...")
            self.generate_favicons(source, output, app_name)

        elif event.button.id == "btn-show-html":
            from shared.favicon_lab import FaviconManager
            manager = FaviconManager()
            html = manager.html()
            self.query_one("#favicon-result", Static).update(f"```html\n{html}\n```")

    @work(thread=True)
    def generate_favicons(self, source: str, output: str, app_name: str) -> None:
        from shared.favicon_lab import FaviconManager
        manager = FaviconManager()

        # Resolve paths relative to project dir if they are not absolute
        src_path = Path(source)
        if not src_path.is_absolute():
            src_path = self.project_dir / src_path

        out_path = Path(output)
        if not out_path.is_absolute():
            out_path = self.project_dir / out_path

        success = manager.generate(str(src_path), str(out_path), app_name=app_name)

        def update_ui():
            if success:
                self.query_one("#favicon-result", Static).update(f"Successfully generated favicons in {out_path}")
            else:
                self.query_one("#favicon-result", Static).update("Failed to generate favicons. Check source path and ensure Pillow is installed.")

        self.app.call_from_thread(update_ui)
