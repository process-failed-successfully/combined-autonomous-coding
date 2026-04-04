"""
Tar Lab TUI
===========

Textual TUI for Tar Lab.
"""

from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Header, Footer, Button, Input, Static, RichLog, Select
from shared.tar_lab import TarManager
from pathlib import Path
import traceback
import asyncio


class TarLabApp(App):
    """A Textual app to manage tar archives."""

    CSS = """
    #input-container {
        height: auto;
        padding: 1;
        border: solid green;
    }
    Input {
        margin-bottom: 1;
    }
    Button {
        margin: 1;
    }
    RichLog {
        border: solid blue;
        height: 1fr;
    }
    """

    BINDINGS = [("d", "toggle_dark", "Toggle dark mode"), ("q", "quit", "Quit")]

    def __init__(self, project_dir=None):
        super().__init__()
        self.manager = TarManager(project_dir)

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Vertical(
            Static("Tar Lab", classes="header"),
            Horizontal(
                Vertical(
                    Input(placeholder="Input path(s) (comma separated for create)", id="input-paths"),
                    Input(placeholder="Output path/dir", id="output-path"),
                    Select([("None", ""), ("gzip", "gz"), ("bzip2", "bz2"), ("xz", "xz")], prompt="Compression", id="compression-select"),
                    id="input-container"
                ),
                Vertical(
                    Button("Create Archive", id="btn-create", variant="success"),
                    Button("Extract Archive", id="btn-extract", variant="primary"),
                    Button("List Contents", id="btn-list", variant="warning"),
                )
            ),
            RichLog(id="log", highlight=True, markup=True)
        )
        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        log = self.query_one(RichLog)
        inputs_str = self.query_one("#input-paths", Input).value.strip()
        output_str = self.query_one("#output-path", Input).value.strip()
        compression_widget = self.query_one("#compression-select", Select)
        compression = compression_widget.value if compression_widget.value != Select.BLANK else ""

        if event.button.id == "btn-create":
            if not inputs_str or not output_str:
                log.write("[red]Error: Input paths and Output path are required for creation.[/red]")
                return

            inputs = [Path(p.strip()) for p in inputs_str.split(",")]
            output = Path(output_str)

            try:
                final_path = await asyncio.to_thread(self.manager.create, inputs, output, compression)
                log.write(f"[green]Archive created at {final_path}[/green]")
            except Exception as e:
                log.write(f"[red]Error creating archive: {e}[/red]")
                log.write(traceback.format_exc())

        elif event.button.id == "btn-extract":
            if not inputs_str:
                log.write("[red]Error: Input path is required for extraction.[/red]")
                return

            input_path = Path(inputs_str)
            output_dir = Path(output_str) if output_str else Path(".")

            try:
                final_path = await asyncio.to_thread(self.manager.extract, input_path, output_dir)
                log.write(f"[green]Archive extracted to {final_path}[/green]")
            except Exception as e:
                log.write(f"[red]Error extracting archive: {e}[/red]")
                log.write(traceback.format_exc())

        elif event.button.id == "btn-list":
            if not inputs_str:
                log.write("[red]Error: Input path is required to list contents.[/red]")
                return

            input_path = Path(inputs_str)

            try:
                contents = await asyncio.to_thread(self.manager.list_contents, input_path)
                log.write(f"[blue]Contents of {input_path}:[/blue]")
                for item in contents:
                    log.write(item)
            except Exception as e:
                log.write(f"[red]Error listing contents: {e}[/red]")
                log.write(traceback.format_exc())


if __name__ == "__main__":
    app = TarLabApp()
    app.run()
