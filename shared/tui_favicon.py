import os
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Label, Button, Input, Static
import warnings

try:
    from shared.favicon_lab import FaviconManager, PILLOW_AVAILABLE
except ImportError:
    PILLOW_AVAILABLE = False


class FaviconLabTab(Vertical):
    """TUI tab for the Favicon Lab."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        if PILLOW_AVAILABLE:
            self.manager = FaviconManager()
        else:
            self.manager = None

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Favicon Lab[/bold]", classes="welcome-text")

            if not PILLOW_AVAILABLE:
                yield Label(
                    "[bold red]Error: Pillow library is not installed.[/bold red]\n"
                    "Install it using `pip install Pillow` to enable Favicon generation.",
                    classes="error-label"
                )
                return

            with Horizontal(classes="stat-box"):
                yield Label("Source Image:", classes="input-label")
                yield Input(placeholder="path/to/logo.png", id="favicon-input")

            with Horizontal(classes="stat-box"):
                yield Label("Output Dir:", classes="input-label")
                yield Input(value=".", id="favicon-output")
                yield Button("Generate Favicons", id="btn-favicon-generate", variant="primary")

            with Vertical(classes="stat-box"):
                yield Label("[bold]HTML Tags[/bold]")
                yield Static(self.manager.html(), id="favicon-html-out", markup=False)

            yield Label("", id="favicon-status", classes="status-label")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-favicon-generate":
            if not self.manager:
                return

            input_path = self.query_one("#favicon-input", Input).value.strip()
            output_dir = self.query_one("#favicon-output", Input).value.strip()

            if not input_path:
                self.query_one("#favicon-status", Label).update("[red]Please specify an input image.[/red]")
                return

            self.query_one("#favicon-status", Label).update("Generating...")

            # Since generate is blocking and does file I/O, we can run it in a worker thread if needed
            # but for simple images it's fast enough. Let's just call it.
            success = self.manager.generate(input_path, output_dir)

            if success:
                self.query_one("#favicon-status", Label).update(f"[green]Successfully generated favicons in {output_dir}[/green]")
            else:
                self.query_one("#favicon-status", Label).update("[red]Error generating favicons. See console for details.[/red]")
