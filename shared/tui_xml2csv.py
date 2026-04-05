from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Button, TextArea, Static
from textual.binding import Binding

try:
    from shared.xml2csv_lab import Xml2CsvManager
except ImportError:
    Xml2CsvManager = None


class Xml2CsvTab(Vertical):
    """A TUI tab for converting XML to CSV."""

    BINDINGS = [
        Binding("ctrl+r", "convert", "Convert", show=True),
    ]

    def compose(self) -> ComposeResult:
        with Horizontal(id="xml2csv-controls", classes="mb-1"):
            yield Button("Convert (Ctrl+R)", id="btn-convert-xml2csv", variant="primary")
            yield Static(" XML \u2192 CSV", classes="text-bold ml-2 py-1")

        with Horizontal(id="xml2csv-panels"):
            with Vertical(classes="w-1-2 pr-1"):
                yield Static("XML Input", classes="text-bold mb-1")
                xml_area = TextArea(id="input-xml")
                # Removed language attribute default for generic text area since xml might not be registered
                yield xml_area

            with Vertical(classes="w-1-2 pl-1"):
                yield Static("CSV Output", classes="text-bold mb-1")
                csv_area = TextArea(id="output-csv-xml2csv", read_only=True)
                yield csv_area

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-convert-xml2csv":
            self.action_convert()

    def action_convert(self) -> None:
        if not Xml2CsvManager:
            self.app.notify("Xml2CsvManager not found.", severity="error")
            return

        xml_input = self.query_one("#input-xml", TextArea).text.strip()
        output_area = self.query_one("#output-csv-xml2csv", TextArea)

        if not xml_input:
            output_area.load_text("")
            return

        try:
            manager = Xml2CsvManager()
            csv_result = manager.convert(xml_input)
            output_area.load_text(csv_result)
            self.app.notify("Conversion successful", severity="information")
        except Exception as e:
            output_area.load_text(f"Error:\n{str(e)}")
            self.app.notify("Conversion failed", severity="error")
