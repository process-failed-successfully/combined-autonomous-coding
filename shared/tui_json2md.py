import json
import pyperclip
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, TextArea, Button
from textual import on

from shared.json2md_lab import Json2MdManager

class Json2MdTab(Container):
    """Tab for converting JSON to Markdown table."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = Json2MdManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]JSON to Markdown Table Converter[/bold]", classes="welcome-text")

            with Horizontal():
                with Vertical(classes="stat-box"):
                    yield Label("Input JSON:")
                    yield TextArea(id="json2md-input", language="json")

                    with Horizontal():
                        yield Button("Convert", id="btn-json2md-convert", variant="primary")
                        yield Button("Clear", id="btn-json2md-clear", variant="error")

                with Vertical(classes="stat-box"):
                    yield Label("Output Markdown Table:")
                    yield TextArea(id="json2md-output", language="markdown", read_only=True)

                    yield Button("Copy to Clipboard", id="btn-json2md-copy", variant="success")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-json2md-convert":
            self.convert()
        elif event.button.id == "btn-json2md-clear":
            self.query_one("#json2md-input", TextArea).text = ""
            self.query_one("#json2md-output", TextArea).text = ""
        elif event.button.id == "btn-json2md-copy":
            self.copy_to_clipboard()

    def convert(self) -> None:
        input_text = self.query_one("#json2md-input", TextArea).text.strip()
        if not input_text:
            self.app.notify("Please enter JSON to convert.", severity="warning")
            return

        try:
            data = json.loads(input_text)
            md_table = self.manager.convert(data)
            self.query_one("#json2md-output", TextArea).text = md_table
            self.app.notify("Conversion successful.", severity="information")
        except json.JSONDecodeError as e:
            self.app.notify(f"Invalid JSON: {e}", severity="error")
        except Exception as e:
            self.app.notify(f"Conversion error: {e}", severity="error")

    def copy_to_clipboard(self) -> None:
        output_text = self.query_one("#json2md-output", TextArea).text
        if not output_text:
            self.app.notify("Nothing to copy.", severity="warning")
            return

        try:
            pyperclip.copy(output_text)
            self.app.notify("Copied to clipboard.", severity="information")
        except Exception as e:
            self.app.notify(f"Failed to copy: {e}", severity="error")
