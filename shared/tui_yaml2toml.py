from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Button, TextArea, Select, Label
from textual.binding import Binding
from shared.yaml2toml_lab import Yaml2TomlManager


class Yaml2TomlLabTab(Static):
    """TUI tab for Yaml2Toml Lab."""

    BINDINGS = [
        Binding("ctrl+r", "convert", "Convert", show=True),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.manager = Yaml2TomlManager()

    def compose(self) -> ComposeResult:
        with Vertical(id="yaml2toml-container", classes="p-1"):
            yield Static("YAML / TOML Converter", classes="text-bold text-center p-1 bg-primary text-primary-content")

            with Horizontal(classes="h-auto p-1 border-b border-primary"):
                yield Label("Mode:", classes="p-1 mt-1")
                yield Select(
                    [("YAML to TOML", "yaml2toml"), ("TOML to YAML", "toml2yaml")],
                    value="yaml2toml",
                    id="yaml2toml-mode-select",
                    classes="w-1-3 m-1"
                )
                yield Button("Convert (Ctrl+R)", id="yaml2toml-convert-btn", variant="primary", classes="m-1")

            with Horizontal(classes="h-full"):
                with Vertical(classes="w-1-2 p-1 border-r border-primary h-full"):
                    yield Label("Input:", classes="text-bold mb-1")
                    yield TextArea(id="yaml2toml-input-ta", classes="h-full")

                with Vertical(classes="w-1-2 p-1 h-full"):
                    yield Label("Output:", classes="text-bold mb-1")
                    yield TextArea(id="yaml2toml-output-ta", classes="h-full", read_only=True)

            yield Static("", id="yaml2toml-status", classes="p-1 h-auto")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yaml2toml-convert-btn":
            await self.action_convert()

    async def action_convert(self) -> None:
        mode_select = self.query_one("#yaml2toml-mode-select", Select)
        input_ta = self.query_one("#yaml2toml-input-ta", TextArea)
        output_ta = self.query_one("#yaml2toml-output-ta", TextArea)
        status_static = self.query_one("#yaml2toml-status", Static)

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
            if mode == "yaml2toml":
                result = self.manager.convert_yaml_to_toml(input_text)
                output_ta.language = "toml"
            elif mode == "toml2yaml":
                result = self.manager.convert_toml_to_yaml(input_text)
                output_ta.language = "yaml"
            else:
                status_static.update(f"[red]Unknown mode: {mode}[/red]")
                return

            output_ta.text = result
            status_static.update("[green]Conversion successful.[/green]")
        except Exception as e:
            output_ta.text = ""
            status_static.update(f"[red]Error: {e}[/red]")
