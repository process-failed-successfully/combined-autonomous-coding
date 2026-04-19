from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Button, TextArea, Input, Label
from textual.binding import Binding
from shared.json2java_lab import Json2JavaManager


class Json2JavaLabTab(Static):
    """TUI tab for Json2Java Lab."""

    BINDINGS = [
        Binding("ctrl+r", "convert", "Convert", show=True),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.manager = Json2JavaManager()

    def compose(self) -> ComposeResult:
        with Vertical(id="json2java-container", classes="p-1"):
            yield Static("JSON to Java Classes Converter", classes="text-bold text-center p-1 bg-primary text-primary-content")

            with Horizontal(classes="h-auto p-1 border-b border-primary"):
                yield Label("Root Class:", classes="p-1 mt-1")
                yield Input(value="RootObject", id="json2java-name-input", classes="w-1-4 m-1")

                yield Label("Package:", classes="p-1 mt-1")
                yield Input(value="", id="json2java-package-input", placeholder="com.example", classes="w-1-4 m-1")

                yield Button("Convert (Ctrl+R)", id="json2java-convert-btn", variant="primary", classes="m-1")

            with Horizontal(classes="h-full"):
                with Vertical(classes="w-1-2 p-1 border-r border-primary h-full"):
                    yield Label("Input JSON:", classes="text-bold mb-1")
                    yield TextArea(id="json2java-input-ta", language="json", classes="h-full")

                with Vertical(classes="w-1-2 p-1 h-full"):
                    yield Label("Output Java:", classes="text-bold mb-1")
                    yield TextArea(id="json2java-output-ta", language="java", classes="h-full", read_only=True)

            yield Static("", id="json2java-status", classes="p-1 h-auto")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "json2java-convert-btn":
            await self.action_convert()

    async def action_convert(self) -> None:
        input_ta = self.query_one("#json2java-input-ta", TextArea)
        output_ta = self.query_one("#json2java-output-ta", TextArea)
        name_input = self.query_one("#json2java-name-input", Input)
        package_input = self.query_one("#json2java-package-input", Input)
        status_static = self.query_one("#json2java-status", Static)

        input_text = input_ta.text.strip()
        root_name = name_input.value.strip() or "RootObject"
        package_name = package_input.value.strip()

        if not input_text:
            status_static.update("[yellow]Input JSON is empty.[/yellow]")
            output_ta.text = ""
            return

        try:
            result = self.manager.convert(input_text, root_name, package_name)
            output_ta.text = result
            status_static.update("[green]Conversion successful.[/green]")
        except ValueError as e:
            output_ta.text = ""
            status_static.update(f"[red]{e}[/red]")
        except Exception as e:
            output_ta.text = ""
            status_static.update(f"[red]Error: {e}[/red]")
