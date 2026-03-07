from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Input, Button, Label, Select, Static
from textual import on

from shared.barcode_lab import BarcodeLabManager

class BarcodeLabTab(Vertical):
    """TUI tab for the Barcode Lab."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.manager = BarcodeLabManager()
        self.formats = []
        try:
            self.formats = self.manager.list_formats()
        except ImportError:
            self.formats = []

    def compose(self) -> ComposeResult:
        with Vertical(id="barcode-lab-container", classes="lab-container"):
            yield Label("Barcode Lab", classes="lab-header")

            if not self.formats:
                yield Label("python-barcode is not installed. Run: pip install python-barcode", classes="error-label")
                return

            with Horizontal(classes="input-row"):
                yield Label("Data:")
                yield Input(placeholder="Enter data to encode", id="barcode-data-input")

            with Horizontal(classes="input-row"):
                yield Label("Format:")
                options = [(f, f) for f in self.formats]
                yield Select(options, id="barcode-format-select", value="code128")

            with Horizontal(classes="input-row"):
                yield Label("Save As (optional path):")
                yield Input(placeholder="e.g. my_barcode", id="barcode-output-input")

            with Horizontal(classes="button-row"):
                yield Button("Generate PNG", id="btn-barcode-gen-png", variant="primary")
                yield Button("Generate SVG", id="btn-barcode-gen-svg")

            with Vertical(classes="result-section"):
                yield Label("Result:")
                yield Static(id="barcode-result-display", classes="result-display")

    @on(Button.Pressed, "#btn-barcode-gen-png")
    def on_generate_png(self, event: Button.Pressed) -> None:
        self.generate_barcode(svg=False)

    @on(Button.Pressed, "#btn-barcode-gen-svg")
    def on_generate_svg(self, event: Button.Pressed) -> None:
        self.generate_barcode(svg=True)

    def generate_barcode(self, svg: bool) -> None:
        data_input = self.query_one("#barcode-data-input", Input)
        format_select = self.query_one("#barcode-format-select", Select)
        output_input = self.query_one("#barcode-output-input", Input)
        result_display = self.query_one("#barcode-result-display", Static)

        data = data_input.value.strip()
        fmt = format_select.value
        output_path = output_input.value.strip()

        if not data:
            result_display.update("Error: Data is required.")
            return

        if not fmt:
            result_display.update("Error: Format is required.")
            return

        try:
            from pathlib import Path
            path = Path(output_path) if output_path else None
            result = self.manager.generate(data, fmt=fmt, output_path=path, svg=svg)
            result_display.update(f"[bold green]Success![/bold green]\n{result}")
        except Exception as e:
            result_display.update(f"[bold red]Error:[/bold red]\n{str(e)}")
