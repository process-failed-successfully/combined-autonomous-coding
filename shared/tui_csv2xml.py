from textual.app import ComposeResult
from textual.widgets import TextArea, Button, Static, Input, Select
from textual.containers import Vertical, Horizontal, Container

from shared.csv2xml_lab import Csv2XmlManager


class Csv2XmlTab(Container):
    """A Textual tab for converting CSV to XML."""

    def __init__(self, project_dir=None):
        super().__init__(id="tab-csv2xml")
        self.manager = Csv2XmlManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("CSV to XML Converter", classes="header")

            with Horizontal(id="csv2xml_options", classes="mb-1"):
                with Vertical():
                    yield Static("Root Element:")
                    yield Input("root", id="csv2xml_root_input")
                with Vertical():
                    yield Static("Row Element:")
                    yield Input("item", id="csv2xml_row_input")
                with Vertical():
                    yield Static("Delimiter:")
                    yield Select.from_values([",", ";", "\\t", "|"], value=",", id="csv2xml_delimiter_select")

            with Horizontal():
                with Vertical():
                    yield Static("Input CSV")
                    self.input_area = TextArea(id="csv2xml_input")
                    yield self.input_area

                with Vertical():
                    yield Static("Output XML")
                    self.output_area = TextArea(id="csv2xml_output", read_only=True)
                    yield self.output_area

            with Horizontal(id="csv2xml_buttons"):
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
            self.app.notify("Input CSV cannot be empty.", severity="error")
            return

        if button_id == "btn_convert":
            root_el = self.query_one("#csv2xml_root_input", Input).value or "root"
            row_el = self.query_one("#csv2xml_row_input", Input).value or "item"
            delimiter = self.query_one("#csv2xml_delimiter_select", Select).value or ","

            if delimiter == "\\t":
                delimiter = "\t"

            try:
                # Synchronous call for simplicity as it's a TUI tab
                xml_data = self.manager.convert(input_text, delimiter=delimiter, root_element=root_el, row_element=row_el)
                self.output_area.text = xml_data
                self.app.notify("Converted successfully.")
            except Exception as e:
                self.output_area.text = ""
                self.app.notify(f"Conversion Error: {e}", severity="error")
