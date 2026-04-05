from textual.app import ComposeResult
from textual.widgets import TextArea, Button, Static, Input
from textual.containers import Vertical, Horizontal, Container

from shared.json2sql_lab import Json2SqlManager


class Json2SqlTab(Container):
    """A Textual tab for converting JSON to SQL INSERT statements."""

    def __init__(self, project_dir=None):
        super().__init__(id="tab-json2sql")
        self.manager = Json2SqlManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("JSON to SQL Converter", classes="header")

            with Horizontal():
                yield Static("Table Name: ", classes="label")
                self.table_input = Input(value="data_table", id="json2sql_table_input")
                yield self.table_input

            with Horizontal():
                with Vertical():
                    yield Static("Input JSON")
                    self.input_area = TextArea(id="json2sql_input", language="json")
                    yield self.input_area

                with Vertical():
                    yield Static("Output SQL")
                    self.output_area = TextArea(id="json2sql_output", read_only=True, language="sql")
                    yield self.output_area

            with Horizontal(id="json2sql_buttons"):
                yield Button("Convert to SQL", id="btn_convert_json2sql", variant="primary")
                yield Button("Clear", id="btn_clear_json2sql")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id

        if button_id == "btn_clear_json2sql":
            self.input_area.text = ""
            self.output_area.text = ""
            self.table_input.value = "data_table"
            return

        if button_id == "btn_convert_json2sql":
            input_text = self.input_area.text.strip()
            table_name = self.table_input.value.strip() or "data_table"

            if not input_text:
                self.app.notify("Input JSON cannot be empty.", severity="error")
                return

            try:
                sql_data = self.manager.convert(input_text, table_name)
                self.output_area.text = sql_data
                self.app.notify("Converted successfully.")
            except Exception as e:
                self.output_area.text = f"Error: {e}"
                self.app.notify(f"Conversion Error: {e}", severity="error")
