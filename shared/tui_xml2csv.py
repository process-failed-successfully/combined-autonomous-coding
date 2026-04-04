from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, Button, TextArea
from textual import on
from shared.xml2csv_lab import Xml2CsvManager


class Xml2CsvTab(Container):
    """Tab for converting XML to CSV."""

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]XML to CSV Converter[/bold]", classes="welcome-text")

            with Horizontal(classes="stat-box"):
                with Vertical(classes="input-pane"):
                    yield Label("Input (XML):")
                    # Intentionally omitting language="xml" since Tree-sitter XML might not be installed,
                    # to prevent "No language 'xml' found" errors in some constrained environments
                    # as advised by AGENTS.md memory context.
                    yield TextArea(id="xml2csv-input")
                    yield Button("Convert to CSV", id="btn-convert-xml2csv", variant="primary")

                with Vertical(classes="output-pane"):
                    yield Label("Output (CSV):")
                    yield TextArea(id="xml2csv-output", read_only=True)

    @on(Button.Pressed, "#btn-convert-xml2csv")
    def on_convert(self) -> None:
        input_area = self.query_one("#xml2csv-input", TextArea)
        output_area = self.query_one("#xml2csv-output", TextArea)

        xml_content = input_area.text
        if not xml_content:
            output_area.text = "Error: Input is empty."
            return

        manager = Xml2CsvManager()
        try:
            csv_result = manager.convert_xml_to_csv(xml_content)
            output_area.text = csv_result
        except ValueError as e:
            output_area.text = str(e)
        except Exception as e:
            output_area.text = f"An unexpected error occurred: {e}"
