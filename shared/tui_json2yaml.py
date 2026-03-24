from textual.app import ComposeResult
from textual.widgets import TextArea, Button, Static
from textual.containers import Vertical, Horizontal, Container

from shared.json2yaml_lab import Json2YamlManager

class Json2YamlTab(Container):
    """A Textual tab for converting JSON to YAML."""

    def __init__(self, project_dir=None):
        super().__init__(id="tab-json2yaml")
        self.manager = Json2YamlManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("JSON to YAML Converter", classes="header")

            with Horizontal():
                with Vertical():
                    yield Static("Input JSON")
                    self.input_area = TextArea(id="json2yaml_input", language="json")
                    yield self.input_area

                with Vertical():
                    yield Static("Output YAML")
                    self.output_area = TextArea(id="json2yaml_output", language="yaml", read_only=True)
                    yield self.output_area

            with Horizontal(id="json2yaml_buttons"):
                yield Button("Convert to YAML", id="btn_convert_json2yaml", variant="primary")
                yield Button("Clear", id="btn_clear_json2yaml", variant="error")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id

        if button_id == "btn_clear_json2yaml":
            self.input_area.text = ""
            self.output_area.text = ""
            return

        input_text = self.input_area.text.strip()
        if not input_text:
            self.app.notify("Input JSON cannot be empty.", severity="warning")
            return

        if button_id == "btn_convert_json2yaml":
            try:
                yaml_data = self.manager.convert(input_text)
                self.output_area.text = yaml_data
                self.app.notify("Converted successfully.", severity="information")
            except Exception as e:
                self.app.notify(f"Conversion Error: {e}", severity="error")
