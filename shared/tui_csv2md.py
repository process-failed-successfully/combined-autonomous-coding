from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Label, Button, Input, TextArea
from textual import on

from shared.csv2md_lab import Csv2MdManager


class Csv2MdTab(Vertical):
    """Tab for CSV to Markdown conversion."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = Csv2MdManager()

    def compose(self) -> ComposeResult:
        yield Label("[bold]CSV to Markdown Converter[/bold]", classes="welcome-text")

        with Horizontal(classes="stat-box"):
            yield Label("Delimiter: ")
            yield Input(value=",", id="csv2md-delimiter", classes="small-input")
            yield Button("Convert", id="btn-csv2md-convert", variant="primary")
            yield Button("Clear", id="btn-csv2md-clear", variant="error")

        with Horizontal():
            with Vertical(classes="stat-box"):
                yield Label("[bold]CSV Input[/bold]")
                yield TextArea(id="csv2md-input")

            with Vertical(classes="stat-box"):
                yield Label("[bold]Markdown Output[/bold]")
                yield TextArea(id="csv2md-output", language="markdown", read_only=True)

    @on(Button.Pressed, "#btn-csv2md-convert")
    def convert_csv(self) -> None:
        input_text = self.query_one("#csv2md-input", TextArea).text
        delimiter = self.query_one("#csv2md-delimiter", Input).value

        if not input_text:
            self.app.notify("Input text cannot be empty.", severity="warning")
            return

        if not delimiter:
            delimiter = ","

        try:
            result = self.manager.convert(input_text, delimiter=delimiter)
            self.query_one("#csv2md-output", TextArea).text = result
            self.app.notify("Conversion successful.")
        except Exception as e:
            self.query_one("#csv2md-output", TextArea).text = f"Error: {e}"
            self.app.notify("Conversion failed.", severity="error")

    @on(Button.Pressed, "#btn-csv2md-clear")
    def clear_text(self) -> None:
        self.query_one("#csv2md-input", TextArea).text = ""
        self.query_one("#csv2md-output", TextArea).text = ""
