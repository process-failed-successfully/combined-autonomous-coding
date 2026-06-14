from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Button, TextArea, Label
from textual.binding import Binding
from shared.jsonl2csv_lab import Jsonl2CsvManager

class Jsonl2CsvLabTab(Static):
    """TUI tab for Jsonl2Csv Lab."""

    BINDINGS = [
        Binding("ctrl+r", "run_conversion", "Convert to CSV", show=True),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.manager = Jsonl2CsvManager()

    def compose(self) -> ComposeResult:
        with Vertical(id="jsonl2csv-container", classes="p-1"):
            yield Static("JSON Lines to CSV Converter", classes="text-bold text-center p-1 bg-primary text-primary-content")

            with Horizontal(classes="h-auto p-1 border-b border-primary justify-between"):
                yield Label("Paste JSON Lines below and convert", classes="mt-1")
                yield Button("Convert (Ctrl+R)", id="jsonl2csv-run-btn", variant="primary", classes="m-1")

            with Horizontal(classes="h-full"):
                with Vertical(classes="w-1-2 p-1 border-r border-primary h-full"):
                    yield Label("JSON Lines Input:", classes="text-bold mb-1")
                    yield TextArea(id="jsonl2csv-input-ta", classes="h-full")

                with Vertical(classes="w-1-2 p-1 h-full"):
                    yield Label("CSV Output:", classes="text-bold mb-1")
                    yield TextArea(id="jsonl2csv-output-ta", classes="h-full", read_only=True)

            yield Static("", id="jsonl2csv-status", classes="p-1 h-auto")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "jsonl2csv-run-btn":
            await self.action_run_conversion()

    async def action_run_conversion(self) -> None:
        input_ta = self.query_one("#jsonl2csv-input-ta", TextArea)
        output_ta = self.query_one("#jsonl2csv-output-ta", TextArea)
        status_static = self.query_one("#jsonl2csv-status", Static)

        input_text = input_ta.text.strip()

        if not input_text:
            status_static.update("[yellow]Input is empty.[/yellow]")
            output_ta.text = ""
            return

        try:
            result = self.manager.convert(input_text)
            output_ta.text = result
            status_static.update("[green]Conversion successful.[/green]")
        except Exception as e:
            output_ta.text = ""
            status_static.update(f"[red]Error: {e}[/red]")
