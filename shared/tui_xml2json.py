import json
from pathlib import Path
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, TextArea, Button
from textual import on

from shared.xml2json_lab import Xml2JsonManager

class Xml2JsonTab(Container):
    """
    XML to JSON conversion tab.
    """
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = Xml2JsonManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]XML to JSON Converter[/bold]", classes="welcome-text")

            with Horizontal():
                with Vertical(classes="stat-box"):
                    yield Label("[bold]Input XML[/bold]")
                    yield TextArea(id="xml2json-input")
                    yield Button("Convert to JSON", id="btn-convert-xml2json", variant="primary")

                with Vertical(classes="stat-box"):
                    yield Label("[bold]Output JSON[/bold]")
                    yield TextArea(id="xml2json-output", read_only=True)

    @on(Button.Pressed, "#btn-convert-xml2json")
    def on_convert(self) -> None:
        xml_input = self.query_one("#xml2json-input", TextArea).text
        output_area = self.query_one("#xml2json-output", TextArea)

        if not xml_input.strip():
            self.notify("Please enter XML to convert.", severity="warning")
            return

        try:
            data = self.manager.convert_string(xml_input)
            output_area.text = json.dumps(data, indent=2)
            self.notify("Conversion successful.")
        except Exception as e:
            output_area.text = f"Error: {e}"
            self.notify("Conversion failed.", severity="error")
