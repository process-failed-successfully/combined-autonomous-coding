from textual.app import ComposeResult
from textual.widgets import TextArea, Button, Static, Label
from textual.containers import Vertical, Horizontal, Container

from shared.xml2csv_lab import Xml2CsvManager


class Xml2CsvTab(Container):
    """A Textual tab for converting XML to CSV."""

    def __init__(self, project_dir=None):
        super().__init__(id="tab-xml2csv")
        self.manager = Xml2CsvManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]XML to CSV Converter[/bold]", classes="header")

            with Horizontal():
                with Vertical():
                    yield Label("[bold]Input XML[/bold]")
                    self.input_area = TextArea(id="xml2csv-input")
                    yield self.input_area

                with Vertical():
                    yield Label("[bold]Output CSV[/bold]")
                    self.output_area = TextArea(id="xml2csv-output", read_only=True)
                    yield self.output_area

            with Horizontal(id="xml2csv-buttons"):
                yield Button("Convert to CSV", id="btn-convert-xml2csv", variant="primary")
                yield Button("Clear", id="btn-clear-xml2csv")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id

        if button_id == "btn-clear-xml2csv":
            self.input_area.load_text("")
            self.output_area.load_text("")
            return

        input_text = self.input_area.text.strip()
        if not input_text:
            self.app.notify("Input XML cannot be empty.", severity="error")
            return

        if button_id == "btn-convert-xml2csv":
            try:
                csv_data = self.manager.convert(input_text)
                self.output_area.load_text(csv_data)
                self.app.notify("Converted successfully.")
            except Exception as e:
                self.app.notify(f"Conversion Error: {e}", severity="error")
