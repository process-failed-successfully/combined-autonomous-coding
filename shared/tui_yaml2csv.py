from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Button, TextArea, Label
from textual.binding import Binding
from shared.yaml2csv_lab import Yaml2CsvManager


class Yaml2CsvTab(Static):
    """TUI tab for Yaml2Csv Lab."""

    BINDINGS = [
        Binding("ctrl+r", "convert", "Convert", show=True),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.manager = Yaml2CsvManager()

    def compose(self) -> ComposeResult:
        with Vertical(id="yaml2csv-container", classes="p-1"):
            yield Static("YAML to CSV Converter", classes="text-bold text-center p-1 bg-primary text-primary-content")

            with Horizontal(classes="h-auto p-1 border-b border-primary"):
                yield Button("Convert (Ctrl+R)", id="yaml2csv-convert-btn", variant="primary", classes="m-1")

            with Horizontal(classes="h-full"):
                with Vertical(classes="w-1-2 p-1 border-r border-primary h-full"):
                    yield Label("Input (YAML):", classes="text-bold mb-1")
                    # Try to set language but don't fail if missing
                    ta_input = TextArea(id="yaml2csv-input-ta", classes="h-full")
                    try:
                        ta_input.language = "yaml"
                    except Exception:
                        pass
                    yield ta_input

                with Vertical(classes="w-1-2 p-1 h-full"):
                    yield Label("Output (CSV):", classes="text-bold mb-1")
                    yield TextArea(id="yaml2csv-output-ta", classes="h-full", read_only=True)

            yield Static("", id="yaml2csv-status", classes="p-1 h-auto")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yaml2csv-convert-btn":
            await self.action_convert()

    async def action_convert(self) -> None:
        input_ta = self.query_one("#yaml2csv-input-ta", TextArea)
        output_ta = self.query_one("#yaml2csv-output-ta", TextArea)
        status_static = self.query_one("#yaml2csv-status", Static)

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
