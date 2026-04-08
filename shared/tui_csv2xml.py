"""
TUI component for CSV to XML conversion.
"""

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import TabPane, Label, Input, Button, TextArea
from textual.binding import Binding

from shared.csv2xml_lab import Csv2XmlManager

class Csv2XmlLabTab(TabPane):
    """Tab for converting CSV to XML."""

    BINDINGS = [
        Binding("ctrl+r", "convert", "Convert CSV to XML", show=True),
        Binding("ctrl+c", "clear_all", "Clear", show=True)
    ]

    def __init__(self, **kwargs):
        super().__init__("CSV2XML Lab", **kwargs)
        self.manager = Csv2XmlManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("CSV to XML Converter", classes="header-label")
            with Horizontal(classes="controls-container", id="c2x-controls"):
                yield Input(placeholder="Delimiter (,)", id="c2x-delimiter", classes="w-1-4")
                yield Input(placeholder="Root name (root)", id="c2x-root", classes="w-1-4")
                yield Input(placeholder="Item name (item)", id="c2x-item", classes="w-1-4")
                yield Button("Convert", id="c2x-convert", variant="primary", classes="w-1-4")

            with Horizontal(classes="editors-container"):
                with Vertical(classes="editor-pane"):
                    yield Label("Input CSV:")
                    yield TextArea(id="c2x-input")
                with Vertical(classes="editor-pane"):
                    yield Label("Output XML:")
                    yield TextArea(id="c2x-output", read_only=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "c2x-convert":
            self.action_convert()

    def action_convert(self) -> None:
        """Converts the CSV to XML."""
        input_widget = self.query_one("#c2x-input", TextArea)
        output_widget = self.query_one("#c2x-output", TextArea)
        delimiter_widget = self.query_one("#c2x-delimiter", Input)
        root_widget = self.query_one("#c2x-root", Input)
        item_widget = self.query_one("#c2x-item", Input)

        csv_data = input_widget.text
        if not csv_data.strip():
            output_widget.text = ""
            return

        delimiter = delimiter_widget.value or ","
        root_name = root_widget.value or "root"
        item_name = item_widget.value or "item"

        try:
            xml_output = self.manager.convert(
                csv_data,
                delimiter=delimiter,
                root_name=root_name,
                item_name=item_name
            )
            output_widget.text = xml_output
        except Exception as e:
            output_widget.text = f"Error during conversion:\n{e}"

    def action_clear_all(self) -> None:
        """Clears all inputs and outputs."""
        self.query_one("#c2x-input", TextArea).text = ""
        self.query_one("#c2x-output", TextArea).text = ""
        self.query_one("#c2x-delimiter", Input).value = ""
        self.query_one("#c2x-root", Input).value = ""
        self.query_one("#c2x-item", Input).value = ""
