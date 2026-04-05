from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Button, TextArea, Input, Label
from textual.binding import Binding
from shared.toml2csv_lab import Toml2CsvManager

class Toml2CsvLabTab(Static):
    """TUI tab for Toml2Csv Lab."""

    BINDINGS = [
        Binding("ctrl+r", "convert", "Convert", show=True),
    ]

    def __init__(self, **kwargs):
        super().__init__(id="tab-toml2csv", **kwargs)
        self.manager = Toml2CsvManager()

    def compose(self) -> ComposeResult:
        with Vertical(id="toml2csv-container", classes="p-1"):
            yield Static("TOML to CSV Converter", classes="text-bold text-center p-1 bg-primary text-primary-content")

            with Horizontal(classes="h-auto p-1 border-b border-primary"):
                yield Label("Delimiter:", classes="p-1 mt-1")
                yield Input(value=",", id="toml2csv-delimiter-input", classes="w-1-6 m-1")
                yield Button("Convert (Ctrl+R)", id="toml2csv-convert-btn", variant="primary", classes="m-1")

            with Horizontal(classes="h-full"):
                with Vertical(classes="w-1-2 p-1 border-r border-primary h-full"):
                    yield Label("Input (TOML):", classes="text-bold mb-1")
                    yield TextArea(id="toml2csv-input-ta", classes="h-full")

                with Vertical(classes="w-1-2 p-1 h-full"):
                    yield Label("Output (CSV):", classes="text-bold mb-1")
                    yield TextArea(id="toml2csv-output-ta", classes="h-full", read_only=True)

            yield Static("", id="toml2csv-status", classes="p-1 h-auto")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "toml2csv-convert-btn":
            await self.action_convert()

    async def action_convert(self) -> None:
        delimiter_input = self.query_one("#toml2csv-delimiter-input", Input)
        input_ta = self.query_one("#toml2csv-input-ta", TextArea)
        output_ta = self.query_one("#toml2csv-output-ta", TextArea)
        status_static = self.query_one("#toml2csv-status", Static)

        delimiter = delimiter_input.value or ","
        input_text = input_ta.text.strip()

        if not input_text:
            status_static.update("[yellow]Input is empty.[/yellow]")
            output_ta.text = ""
            return

        try:
            result = self.manager.convert(input_text, delimiter=delimiter)
            output_ta.text = result
            status_static.update("[green]Conversion successful.[/green]")
        except Exception as e:
            output_ta.text = ""
            status_static.update(f"[red]Error: {e}[/red]")
