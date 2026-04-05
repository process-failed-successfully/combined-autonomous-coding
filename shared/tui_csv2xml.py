from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Input, Label, TextArea
from textual import on
from shared.csv2xml_lab import Csv2XmlManager


class Csv2XmlTab(Container):
    """
    CSV to XML conversion tab.
    """
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = Csv2XmlManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]CSV to XML Converter[/bold]", classes="welcome-text")

            with Horizontal():
                with Vertical(classes="stat-box", id="csv2xml-left-pane"):
                    yield Label("Delimiter (e.g. ',' or ';'):")
                    yield Input(value=",", id="csv2xml-delimiter", classes="config-input")

                    yield Label("Root Tag:")
                    yield Input(value="root", id="csv2xml-root-tag", classes="config-input")

                    yield Label("Row Tag:")
                    yield Input(value="row", id="csv2xml-row-tag", classes="config-input")

                    yield Label("[bold]Input CSV[/bold]")
                    yield TextArea(id="csv2xml-input")
                    yield Button("Convert to XML", id="btn-convert-csv2xml", variant="primary")

                with Vertical(classes="stat-box", id="csv2xml-right-pane"):
                    yield Label("[bold]Output XML[/bold]")
                    yield TextArea(id="csv2xml-output", read_only=True)

    @on(Button.Pressed, "#btn-convert-csv2xml")
    def on_convert(self) -> None:
        csv_input = self.query_one("#csv2xml-input", TextArea).text
        output_area = self.query_one("#csv2xml-output", TextArea)
        delimiter = self.query_one("#csv2xml-delimiter", Input).value or ","
        root_tag = self.query_one("#csv2xml-root-tag", Input).value or "root"
        row_tag = self.query_one("#csv2xml-row-tag", Input).value or "row"

        if not csv_input.strip():
            self.notify("Please enter CSV to convert.", severity="warning")
            output_area.text = ""
            return

        try:
            xml_str = self.manager.convert_string(csv_input, delimiter=delimiter, root_tag=root_tag, row_tag=row_tag)
            output_area.text = xml_str
            self.notify("Conversion successful.")
        except Exception as e:
            output_area.text = f"Error: {e}"
            self.notify("Conversion failed.", severity="error")
