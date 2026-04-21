from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Button, TextArea, Select, Label
from textual.binding import Binding
from shared.yaml2json_lab import Yaml2JsonManager

class Json2YamlLabTab(Static):
    """TUI tab for Json2Yaml Lab."""

    BINDINGS = [
        Binding("ctrl+r", "convert", "Convert", show=True),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.manager = Yaml2JsonManager()

    def compose(self) -> ComposeResult:
        with Vertical(id="json2yaml-container", classes="p-1"):
            yield Static("JSON / YAML Converter", classes="text-bold text-center p-1 bg-primary text-primary-content")

            with Horizontal(classes="h-auto p-1 border-b border-primary"):
                yield Label("Mode:", classes="p-1 mt-1")
                yield Select(
                    [("JSON to YAML", "json2yaml"), ("YAML to JSON", "yaml2json")],
                    value="json2yaml",
                    id="json2yaml-mode-select",
                    classes="w-1-3 m-1"
                )
                yield Button("Convert (Ctrl+R)", id="json2yaml-convert-btn", variant="primary", classes="m-1")

            with Horizontal(classes="h-full"):
                with Vertical(classes="w-1-2 p-1 border-r border-primary h-full"):
                    yield Label("Input:", classes="text-bold mb-1")
                    yield TextArea(id="json2yaml-input-ta", classes="h-full")

                with Vertical(classes="w-1-2 p-1 h-full"):
                    yield Label("Output:", classes="text-bold mb-1")
                    yield TextArea(id="json2yaml-output-ta", classes="h-full", read_only=True)

            yield Static("", id="json2yaml-status", classes="p-1 h-auto")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "json2yaml-convert-btn":
            await self.action_convert()

    async def action_convert(self) -> None:
        mode_select = self.query_one("#json2yaml-mode-select", Select)
        input_ta = self.query_one("#json2yaml-input-ta", TextArea)
        output_ta = self.query_one("#json2yaml-output-ta", TextArea)
        status_static = self.query_one("#json2yaml-status", Static)

        mode = mode_select.value
        input_text = input_ta.text.strip()

        if mode == Select.BLANK or not isinstance(mode, str):
            status_static.update("[red]Please select a conversion mode.[/red]")
            return

        if not input_text:
            status_static.update("[yellow]Input is empty.[/yellow]")
            output_ta.text = ""
            return

        try:
            if mode == "yaml2json":
                result = self.manager.convert_yaml_to_json(input_text)
                output_ta.language = "json"
            elif mode == "json2yaml":
                result = self.manager.convert_json_to_yaml(input_text)
                output_ta.language = "yaml"
            else:
                status_static.update(f"[red]Unknown mode: {mode}[/red]")
                return

            output_ta.text = result
            status_static.update("[green]Conversion successful.[/green]")
        except Exception as e:
            output_ta.text = ""
            status_static.update(f"[red]Error: {e}[/red]")
