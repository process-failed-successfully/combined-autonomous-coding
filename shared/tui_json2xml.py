from textual.app import ComposeResult
from textual.widgets import TextArea, Button, Static
from textual.containers import Vertical, Horizontal, Container

from shared.json2xml_lab import Json2XmlManager


class Json2XmlTab(Container):
    """A Textual tab for converting JSON to XML."""

    def __init__(self, project_dir=None):
        super().__init__(id="tab-json2xml")
        self.manager = Json2XmlManager(project_dir)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("JSON to XML Converter", classes="header")

            with Horizontal():
                with Vertical():
                    yield Static("Input JSON")
                    self.input_area = TextArea(id="json2xml_input", language="json")
                    yield self.input_area

                with Vertical():
                    yield Static("Output XML")
                    self.output_area = TextArea(id="json2xml_output", language="xml", read_only=True)
                    yield self.output_area

            with Horizontal(id="json2xml_buttons"):
                yield Button("Convert to XML", id="btn_convert", variant="primary")
                yield Button("Clear", id="btn_clear")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id

        if button_id == "btn_clear":
            self.input_area.text = ""
            self.output_area.text = ""
            return

        input_text = self.input_area.text.strip()
        if not input_text:
            self.app.notify("Input JSON cannot be empty.", severity="error")
            return

        if button_id == "btn_convert":
            try:
                xml_data = self.manager.convert(input_text)
                self.output_area.text = xml_data
                self.app.notify("Converted successfully.")
            except Exception as e:
                self.app.notify(f"Conversion Error: {e}", severity="error")
