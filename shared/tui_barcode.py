"""
Barcode Lab TUI Tab
"""

from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Label, Input, Button, RichLog, Select
from textual.message import Message

from shared.barcode_lab import BarcodeLabManager


class BarcodeLabTab(Vertical):
    """TUI Tab for Barcode generation and validation."""

    def __init__(self, project_dir: Path, **kwargs):
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = BarcodeLabManager()
        self.supported_formats = []
        try:
            self.supported_formats = self.manager.get_supported_formats()
        except ImportError:
            pass

    def compose(self) -> ComposeResult:
        yield Label("1D Barcode Generator & Validator", classes="section-title")

        if not self.supported_formats:
            yield Label("python-barcode is not installed. Please install it.", id="barcode-error-msg")
            return

        with Horizontal(classes="input-group"):
            yield Label("Barcode Data:")
            yield Input(placeholder="Enter data to encode", id="barcode-data-input")

        with Horizontal(classes="input-group"):
            yield Label("Barcode Type:")
            options = [(fmt, fmt) for fmt in self.supported_formats]
            yield Select(options, prompt="Select Barcode Type", id="barcode-type-select")

        with Horizontal(classes="input-group"):
            yield Label("Output File Path (for Generation):")
            yield Input(placeholder="e.g., barcode (extension .png will be added)", id="barcode-output-input")

        with Horizontal(classes="button-group"):
            yield Button("Generate Barcode", id="btn-barcode-generate", variant="primary")
            yield Button("Validate Data", id="btn-barcode-validate")

        yield RichLog(id="barcode-log", highlight=True, markup=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        data_input = self.query_one("#barcode-data-input", Input)
        type_select = self.query_one("#barcode-type-select", Select)
        output_input = self.query_one("#barcode-output-input", Input)
        log = self.query_one("#barcode-log", RichLog)

        data = data_input.value.strip()
        barcode_type = type_select.value

        if not data or not barcode_type:
            log.write("[red]Error: Please provide data and select a barcode type.[/red]")
            return

        if event.button.id == "btn-barcode-generate":
            output_path_str = output_input.value.strip()
            if not output_path_str:
                log.write("[red]Error: Please provide an output file path.[/red]")
                return

            try:
                success, msg = self.manager.generate(data, barcode_type, Path(output_path_str))
                if success:
                    log.write(f"[green]✅ {msg}[/green]")
                else:
                    log.write(f"[red]❌ Error generating barcode: {msg}[/red]")
            except Exception as e:
                log.write(f"[red]❌ Exception: {e}[/red]")

        elif event.button.id == "btn-barcode-validate":
            try:
                success, msg = self.manager.validate(data, barcode_type)
                if success:
                    log.write(f"[green]✅ {msg}[/green]")
                else:
                    log.write(f"[red]❌ Error: {msg}[/red]")
            except Exception as e:
                log.write(f"[red]❌ Exception: {e}[/red]")
