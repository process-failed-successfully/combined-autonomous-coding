from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Button, TextArea, Select, Label
from textual.binding import Binding
from shared.json2toml_lab import Json2TomlManager


class Json2TomlLabTab(Static):
    """TUI tab for Json2Toml Lab."""

    BINDINGS = [
        Binding("ctrl+r", "convert", "Convert", show=True),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.manager = Json2TomlManager()

    def compose(self) -> ComposeResult:
        with Vertical(id="json2toml-container", classes="p-1"):
            yield Static("JSON to TOML Converter", classes="text-bold text-center p-1 bg-primary text-primary-content")

            with Horizontal(classes="h-auto p-1 border-b border-primary"):
                yield Button("Convert (Ctrl+R)", id="json2toml-convert-btn", variant="primary", classes="m-1")

            with Horizontal(classes="h-full"):
                with Vertical(classes="w-1-2 p-1 border-r border-primary h-full"):
                    yield Label("Input (JSON):", classes="text-bold mb-1")
                    yield TextArea(id="json2toml-input-ta", classes="h-full", language="json")

                with Vertical(classes="w-1-2 p-1 h-full"):
                    yield Label("Output (TOML):", classes="text-bold mb-1")
                    yield TextArea(id="json2toml-output-ta", classes="h-full", read_only=True, language="toml")

            yield Static("", id="json2toml-status", classes="p-1 h-auto")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "json2toml-convert-btn":
            await self.action_convert()

    async def action_convert(self) -> None:
        input_ta = self.query_one("#json2toml-input-ta", TextArea)
        output_ta = self.query_one("#json2toml-output-ta", TextArea)
        status_static = self.query_one("#json2toml-status", Static)

        input_text = input_ta.text.strip()

        if not input_text:
            status_static.update("[yellow]Input is empty.[/yellow]")
            output_ta.text = ""
            return

        try:
            result = self.manager.convert_json_to_toml(input_text)
            output_ta.text = result
            status_static.update("[green]Conversion successful.[/green]")
        except Exception as e:
            output_ta.text = ""
            status_static.update(f"[red]Error: {e}[/red]")
