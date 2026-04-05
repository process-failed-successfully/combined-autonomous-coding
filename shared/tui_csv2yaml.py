from textual.app import ComposeResult
from textual.widgets import TextArea, Button, Static
from textual.containers import Vertical, Horizontal, Container

from shared.csv2yaml_lab import Csv2YamlManager


class Csv2YamlTab(Container):
    """A Textual tab for converting CSV to YAML."""

    def __init__(self, project_dir=None):
        super().__init__(id="tab-csv2yaml")
        self.manager = Csv2YamlManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("CSV to YAML Converter", classes="header")

            with Horizontal():
                with Vertical():
                    yield Static("Input CSV")
                    self.input_area = TextArea(id="csv2yaml_input")
                    yield self.input_area

                with Vertical():
                    yield Static("Output YAML")
                    self.output_area = TextArea(id="csv2yaml_output", language="yaml", read_only=True)
                    yield self.output_area

            with Horizontal(id="csv2yaml_buttons"):
                yield Button("Convert to YAML", id="btn_convert", variant="primary")
                yield Button("Clear", id="btn_clear")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id

        if button_id == "btn_clear":
            self.input_area.text = ""
            self.output_area.text = ""
            return

        input_text = self.input_area.text.strip()
        if not input_text:
            self.app.notify("Input CSV cannot be empty.", severity="error")
            return

        if button_id == "btn_convert":
            try:
                yaml_data = self.manager.convert(input_text)
                self.output_area.text = yaml_data
                self.app.notify("Converted successfully.")
            except Exception as e:
                self.app.notify(f"Conversion Error: {e}", severity="error")
