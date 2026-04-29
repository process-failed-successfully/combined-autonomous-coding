from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Button, TextArea, Input, Label
from textual.binding import Binding
from shared.json2dart_lab import Json2DartManager


class Json2DartLabTab(Static):
    """TUI tab for Json2Dart Lab."""

    BINDINGS = [
        Binding("ctrl+r", "convert", "Convert", show=True),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.manager = Json2DartManager()

    def compose(self) -> ComposeResult:
        with Vertical(id="json2dart-container", classes="p-1"):
            yield Static("JSON to Dart Converter", classes="text-bold text-center p-1 bg-primary text-primary-content")

            with Horizontal(classes="h-auto p-1 border-b border-primary"):
                yield Label("Root Class Name:", classes="p-1 mt-1")
                yield Input(value="RootClass", id="json2dart-name-input", classes="w-1-3 m-1")
                yield Button("Convert (Ctrl+R)", id="json2dart-convert-btn", variant="primary", classes="m-1")

            with Horizontal(classes="h-full"):
                with Vertical(classes="w-1-2 p-1 border-r border-primary h-full"):
                    yield Label("JSON Input:", classes="text-bold mb-1")
                    yield TextArea(id="json2dart-input-ta", classes="h-full", language="json")

                with Vertical(classes="w-1-2 p-1 h-full"):
                    yield Label("Dart Output:", classes="text-bold mb-1")
                    # Dart is supported in rich/textual textareas, but let's just use generic or java-like if missing
                    # Actually standard generic is fine, or we can omit language if it causes issues.
                    # We will omit language to avoid LanguageDoesNotExist error if textual version lacks 'dart'
                    yield TextArea(id="json2dart-output-ta", classes="h-full", read_only=True)

            yield Static("", id="json2dart-status", classes="p-1 h-auto")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "json2dart-convert-btn":
            await self.action_convert()

    async def action_convert(self) -> None:
        name_input = self.query_one("#json2dart-name-input", Input)
        input_ta = self.query_one("#json2dart-input-ta", TextArea)
        output_ta = self.query_one("#json2dart-output-ta", TextArea)
        status_static = self.query_one("#json2dart-status", Static)

        root_name = name_input.value.strip() or "RootClass"
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
