from textual.app import ComposeResult
from textual.widgets import TabPane, TextArea, Button, Label
from textual.containers import Horizontal, Vertical
from textual import on

from shared.xml2json_lab import Xml2JsonManager


class Xml2JsonTab(TabPane):
    """A tab for converting XML to JSON."""

    def __init__(self, *args, **kwargs):
        super().__init__("XML \u2192 JSON", id="tab-xml2json", *args, **kwargs)
        self.manager = Xml2JsonManager()

    def compose(self) -> ComposeResult:
        with Vertical(classes="p-2 h-full"):
            yield Label("XML to JSON Converter", classes="text-lg text-primary mb-2")

            with Horizontal(classes="h-5-6"):
                with Vertical(classes="w-1-2 pr-2"):
                    yield Label("Input XML:")
                    yield TextArea(
                        id="xml2json-input",
                        classes="h-full border border-primary"
                    )
                with Vertical(classes="w-1-2 pl-2"):
                    yield Label("Output JSON:")
                    yield TextArea(
                        id="xml2json-output",
                        language="json",
                        read_only=True,
                        classes="h-full border border-success"
                    )

            with Horizontal(classes="h-1-6 items-center justify-center mt-2"):
                yield Button("Convert", id="btn-xml2json-convert", variant="primary")
                yield Button("Clear", id="btn-xml2json-clear", variant="error", classes="ml-4")

            yield Label("", id="lbl-xml2json-status", classes="mt-2 text-warning")

    @on(Button.Pressed, "#btn-xml2json-convert")
    def on_convert(self):
        input_area = self.query_one("#xml2json-input", TextArea)
        output_area = self.query_one("#xml2json-output", TextArea)
        status_label = self.query_one("#lbl-xml2json-status", Label)

        xml_text = input_area.text.strip()
        if not xml_text:
            output_area.text = ""
            status_label.update("Please enter XML to convert.")
            return

        try:
            json_text = self.manager.convert(xml_text)
            output_area.text = json_text
            status_label.update("")
        except ValueError as e:
            output_area.text = ""
            status_label.update(f"Error: {e}")
        except Exception as e:
            output_area.text = ""
            status_label.update(f"Unexpected error: {e}")

    @on(Button.Pressed, "#btn-xml2json-clear")
    def on_clear(self):
        self.query_one("#xml2json-input", TextArea).text = ""
        self.query_one("#xml2json-output", TextArea).text = ""
        self.query_one("#lbl-xml2json-status", Label).update("")
