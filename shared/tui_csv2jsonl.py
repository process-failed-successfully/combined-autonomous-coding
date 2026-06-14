from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Button, TextArea, Label, Input
from textual.binding import Binding
from shared.csv2jsonl_lab import Csv2JsonlManager

class Csv2JsonlLabTab(Static):
    """TUI tab for Csv2Jsonl Lab."""

    BINDINGS = [
        Binding("ctrl+r", "run_conversion", "Convert to JSON Lines", show=True),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.manager = Csv2JsonlManager()

    def compose(self) -> ComposeResult:
        with Vertical(id="csv2jsonl-container", classes="p-1"):
            yield Static("CSV to JSON Lines Converter", classes="text-bold text-center p-1 bg-primary text-primary-content")

            with Horizontal(classes="h-auto p-1 border-b border-primary justify-between"):
                with Horizontal(classes="w-auto h-auto"):
                    yield Label("Delimiter:", classes="mt-2 mr-2")
                    yield Input(value=",", id="csv2jsonl-delimiter-input", classes="w-16")
                yield Button("Convert (Ctrl+R)", id="csv2jsonl-run-btn", variant="primary", classes="m-1")

            with Horizontal(classes="h-full"):
                with Vertical(classes="w-1-2 p-1 border-r border-primary h-full"):
                    yield Label("CSV Input:", classes="text-bold mb-1")
                    yield TextArea(id="csv2jsonl-input-ta", classes="h-full")

                with Vertical(classes="w-1-2 p-1 h-full"):
                    yield Label("JSON Lines Output:", classes="text-bold mb-1")
                    yield TextArea(id="csv2jsonl-output-ta", classes="h-full", read_only=True)

            yield Static("", id="csv2jsonl-status", classes="p-1 h-auto")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "csv2jsonl-run-btn":
            await self.action_run_conversion()

    async def action_run_conversion(self) -> None:
        input_ta = self.query_one("#csv2jsonl-input-ta", TextArea)
        output_ta = self.query_one("#csv2jsonl-output-ta", TextArea)
        status_static = self.query_one("#csv2jsonl-status", Static)
        delimiter_input = self.query_one("#csv2jsonl-delimiter-input", Input)

        input_text = input_ta.text.strip()
        delimiter = delimiter_input.value or ","

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
