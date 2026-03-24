from textual.app import ComposeResult
from textual.widgets import TextArea, Button, Static
from textual.containers import Vertical, Horizontal, Container
import json

from shared.yaml2json_lab import Yaml2JsonManager


class Yaml2JsonTab(Container):
    """A Textual tab for converting YAML to JSON."""

    def __init__(self, project_dir=None):
        super().__init__(id="tab-yaml2json")
        self.manager = Yaml2JsonManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("YAML to JSON Converter", classes="header")

            with Horizontal():
                with Vertical():
                    yield Static("Input YAML")
                    self.input_area = TextArea(id="yaml2json_input", language="yaml")
                    yield self.input_area

                with Vertical():
                    yield Static("Output JSON")
                    self.output_area = TextArea(id="yaml2json_output", language="json", read_only=True)
                    yield self.output_area

            with Horizontal(id="yaml2json_buttons"):
                yield Button("Convert to JSON", id="btn_convert_yaml2json", variant="primary")
                yield Button("Clear", id="btn_clear_yaml2json", variant="error")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id

        if button_id == "btn_clear_yaml2json":
            self.input_area.text = ""
            self.output_area.text = ""
            return

        input_text = self.input_area.text.strip()
        if not input_text:
            self.app.notify("Input YAML cannot be empty.", severity="warning")
            return

        if button_id == "btn_convert_yaml2json":
            try:
                json_data = self.manager.convert(input_text)
                self.output_area.text = json.dumps(json_data, indent=2)
                self.app.notify("Converted successfully.", severity="information")
            except Exception as e:
                self.app.notify(f"Conversion Error: {e}", severity="error")
