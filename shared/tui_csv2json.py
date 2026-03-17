from textual.app import ComposeResult
from textual.widgets import TextArea, Button, Static, Input
from textual.containers import Vertical, Horizontal, Container

from shared.csv2json_lab import Csv2JsonManager

class Csv2JsonTab(Container):
    """A Textual tab for converting CSV to JSON."""

    def __init__(self, project_dir=None):
        super().__init__(id="tab-csv2json")
        self.manager = Csv2JsonManager(project_dir)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("CSV to JSON Converter", classes="header")

            with Horizontal():
                with Vertical():
                    yield Static("Input CSV")
                    self.input_area = TextArea(id="csv2json_input", language="csv")
                    yield self.input_area

                with Vertical():
                    yield Static("Output JSON")
                    self.output_area = TextArea(id="csv2json_output", read_only=True, language="json")
                    yield self.output_area

            with Horizontal(id="csv2json_options", classes="my-1"):
                yield Static("Delimiter:", classes="label mt-1")
                self.delimiter_input = Input(value=",", id="csv_delimiter_input")
                yield self.delimiter_input

            with Horizontal(id="csv2json_buttons"):
                yield Button("Convert to JSON", id="btn_convert", variant="primary")
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
                delimiter = self.delimiter_input.value or ","
                # For simplicity, convert synchronously. For very large text, we could use asyncio.to_thread
                json_data = self.manager.convert(input_text, delimiter=delimiter)
                self.output_area.text = json_data
                self.app.notify("Converted successfully.")
            except Exception as e:
                self.app.notify(f"Conversion Error: {e}", severity="error")
