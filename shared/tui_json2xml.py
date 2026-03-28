from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, TextArea, Button
from textual import on

from shared.json2xml_lab import Json2XmlManager


class Json2XmlTab(Container):
    """
    JSON to XML conversion tab.
    """
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = Json2XmlManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]JSON to XML Converter[/bold]", classes="welcome-text")

            with Horizontal():
                with Vertical(classes="stat-box"):
                    yield Label("[bold]Input JSON[/bold]")
                    yield TextArea(id="json2xml-input")
                    yield Button("Convert to XML", id="btn-convert-json2xml", variant="primary")

                with Vertical(classes="stat-box"):
                    yield Label("[bold]Output XML[/bold]")
                    yield TextArea(id="json2xml-output", read_only=True)

    @on(Button.Pressed, "#btn-convert-json2xml")
    def on_convert(self) -> None:
        json_input = self.query_one("#json2xml-input", TextArea).text
        output_area = self.query_one("#json2xml-output", TextArea)

        if not json_input.strip():
            self.notify("Please enter JSON to convert.", severity="warning")
            return

        try:
            xml_str = self.manager.convert_string(json_input)
            output_area.text = xml_str
            self.notify("Conversion successful.")
        except Exception as e:
            output_area.text = f"Error: {e}"
            self.notify("Conversion failed.", severity="error")
