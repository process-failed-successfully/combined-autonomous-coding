from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Label, Button, Input, TextArea
from textual import on

from shared.md2csv_lab import Md2CsvManager

class Md2CsvTab(Vertical):
    """Tab for Markdown to CSV conversion."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.manager = Md2CsvManager()

    def compose(self) -> ComposeResult:
        with Vertical(classes="pl-main-container"):
            yield Label("[bold]Markdown to CSV Converter[/bold]", classes="welcome-text")

            with Horizontal(id="md2csv-controls"):
                yield Label("Delimiter: ", classes="pl-label")
                yield Input(
                    value=",",
                    placeholder="e.g. , or ; or \\t",
                    id="md2csv-delimiter",
                    classes="pl-input-small"
                )
                yield Button("Convert", id="btn-md2csv-convert", variant="primary")

            with Vertical(id="md2csv-input-container"):
                yield Label("Markdown Input:")
                yield TextArea(
                    text="| Header 1 | Header 2 |\n|---|---|\n| Data 1 | Data 2 |",
                    language="markdown",
                    id="md2csv-textarea",
                    classes="pl-textarea"
                )

            with Vertical(id="md2csv-result-container", classes="pl-result-panel"):
                yield Label("CSV Output:")
                yield TextArea(
                    "",
                    id="md2csv-result-textarea",
                    classes="pl-textarea-result",
                    read_only=True
                )
                self.error_label = Label("", id="md2csv-error-text", classes="pl-error")
                yield self.error_label

    def on_mount(self) -> None:
        self.do_conversion()

    @on(TextArea.Changed)
    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        if event.text_area.id == "md2csv-textarea":
            self.do_conversion()

    @on(Input.Changed)
    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "md2csv-delimiter":
            self.do_conversion()

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-md2csv-convert":
            self.do_conversion()

    def do_conversion(self) -> None:
        md_text = self.query_one("#md2csv-textarea", TextArea).text
        delim_text = self.query_one("#md2csv-delimiter", Input).value
        result_area = self.query_one("#md2csv-result-textarea", TextArea)

        self.error_label.update("")

        if not md_text.strip():
            result_area.text = ""
            return

        delimiter = delim_text if delim_text else ","
        if delimiter == "\\t":
            delimiter = "\t"

        try:
            csv_output = self.manager.convert_to_csv(md_text, delimiter=delimiter)
            result_area.text = csv_output
        except Exception as e:
            result_area.text = ""
            self.error_label.update(f"Error: {e}")
