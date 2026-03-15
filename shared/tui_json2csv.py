from textual.app import ComposeResult
from textual.widgets import TextArea, Button, Static
from textual.containers import Vertical, Horizontal, Container
import sys

from shared.json2csv_lab import Json2CsvManager


class Json2CsvTab(Container):
    """A Textual tab for converting JSON to CSV."""

    def __init__(self, project_dir=None):
        super().__init__(id="tab-json2csv")
        self.manager = Json2CsvManager(project_dir)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("JSON to CSV Converter", classes="header")

            with Horizontal():
                with Vertical():
                    yield Static("Input JSON")
                    self.input_area = TextArea(id="json2csv_input", language="json")
                    yield self.input_area

                with Vertical():
                    yield Static("Output CSV")
                    self.output_area = TextArea(id="json2csv_output", read_only=True)
                    yield self.output_area

            with Horizontal(id="json2csv_buttons"):
                yield Button("Convert to CSV", id="btn_convert", variant="primary")
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
                # To prevent blocking the main thread for large JSONs, we could use asyncio.to_thread
                # but for simplicity, we'll do it synchronously here as it's a TUI tab
                csv_data = self.manager.convert(input_text)
                self.output_area.text = csv_data
                self.app.notify("Converted successfully.")
            except Exception as e:
                self.app.notify(f"Conversion Error: {e}", severity="error")
