from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Button, TextArea, Input, Label
from textual.binding import Binding
from shared.json2swift_lab import Json2SwiftManager


class Json2SwiftLabTab(Static):
    """TUI tab for Json2Swift Lab."""

    BINDINGS = [
        Binding("ctrl+r", "convert", "Convert", show=True),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.manager = Json2SwiftManager()

    def compose(self) -> ComposeResult:
        with Vertical(id="json2swift-container", classes="p-1"):
            yield Static("JSON to Swift Converter", classes="text-bold text-center p-1 bg-primary text-primary-content")

            with Horizontal(classes="h-auto p-1 border-b border-primary"):
                yield Label("Root Struct Name:", classes="p-1 mt-1")
                yield Input(value="RootStruct", id="json2swift-name-input", classes="w-1-3 m-1")
                yield Button("Convert (Ctrl+R)", id="json2swift-convert-btn", variant="primary", classes="m-1")

            with Horizontal(classes="h-full"):
                with Vertical(classes="w-1-2 p-1 border-r border-primary h-full"):
                    yield Label("JSON Input:", classes="text-bold mb-1")
                    yield TextArea(id="json2swift-input-ta", classes="h-full", language="json")

                with Vertical(classes="w-1-2 p-1 h-full"):
                    yield Label("Swift Output:", classes="text-bold mb-1")
                    # Using `swift` for language if available, else plain text
                    yield TextArea(id="json2swift-output-ta", classes="h-full", read_only=True)

            yield Static("", id="json2swift-status", classes="p-1 h-auto")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "json2swift-convert-btn":
            await self.action_convert()

    async def action_convert(self) -> None:
        name_input = self.query_one("#json2swift-name-input", Input)
        input_ta = self.query_one("#json2swift-input-ta", TextArea)
        output_ta = self.query_one("#json2swift-output-ta", TextArea)
        status_static = self.query_one("#json2swift-status", Static)

        root_name = name_input.value.strip() or "RootStruct"
        input_text = input_ta.text.strip()

        if not input_text:
            status_static.update("[yellow]Input is empty.[/yellow]")
            output_ta.text = ""
            return

        try:
            result = self.manager.convert(input_text, root_name=root_name)
            output_ta.text = result
            status_static.update("[green]Conversion successful.[/green]")
        except Exception as e:
            output_ta.text = ""
            status_static.update(f"[red]Error: {e}[/red]")
