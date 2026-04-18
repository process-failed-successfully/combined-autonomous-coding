from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Button, TextArea, Input, Label
from textual.binding import Binding
from shared.json2go_lab import Json2GoManager

class Json2GoLabTab(Static):
    """TUI tab for Json2Go Lab."""

    BINDINGS = [
        Binding("ctrl+r", "convert", "Convert", show=True),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.manager = Json2GoManager()

    def compose(self) -> ComposeResult:
        with Vertical(id="json2go-container", classes="p-1"):
            yield Static("JSON to Go Structs Converter", classes="text-bold text-center p-1 bg-primary text-primary-content")

            with Horizontal(classes="h-auto p-1 border-b border-primary"):
                yield Label("Root Struct Name:", classes="p-1 mt-1")
                yield Input(value="RootStruct", id="json2go-name-input", classes="w-1-3 m-1")
                yield Button("Convert (Ctrl+R)", id="json2go-convert-btn", variant="primary", classes="m-1")

            with Horizontal(classes="h-full"):
                with Vertical(classes="w-1-2 p-1 border-r border-primary h-full"):
                    yield Label("Input JSON:", classes="text-bold mb-1")
                    yield TextArea(id="json2go-input-ta", language="json", classes="h-full")

                with Vertical(classes="w-1-2 p-1 h-full"):
                    yield Label("Output Go:", classes="text-bold mb-1")
                    yield TextArea(id="json2go-output-ta", language="go", classes="h-full", read_only=True)

            yield Static("", id="json2go-status", classes="p-1 h-auto")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "json2go-convert-btn":
            await self.action_convert()

    async def action_convert(self) -> None:
        input_ta = self.query_one("#json2go-input-ta", TextArea)
        output_ta = self.query_one("#json2go-output-ta", TextArea)
        name_input = self.query_one("#json2go-name-input", Input)
        status_static = self.query_one("#json2go-status", Static)

        input_text = input_ta.text.strip()
        root_name = name_input.value.strip() or "RootStruct"

        if not input_text:
            status_static.update("[yellow]Input JSON is empty.[/yellow]")
            output_ta.text = ""
            return

        try:
            result = self.manager.convert(input_text, root_name)
            output_ta.text = result
            status_static.update("[green]Conversion successful.[/green]")
        except ValueError as e:
            output_ta.text = ""
            status_static.update(f"[red]{e}[/red]")
        except Exception as e:
            output_ta.text = ""
            status_static.update(f"[red]Error: {e}[/red]")
