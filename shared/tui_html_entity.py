from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, TextArea, Static, Label, Select
from textual import on
import html

class HtmlEntityTab(Container):
    """A Textual tab for the HTML Entity Lab."""

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("Input Text or HTML Entities:"),
            TextArea(id="html-entity-input", classes="h-1-3"),

            Horizontal(
                Button("Encode Entities", id="btn-html-entity-encode", variant="primary"),
                Button("Decode Entities", id="btn-html-entity-decode", variant="primary"),
                Button("Clear", id="btn-html-entity-clear", variant="error"),
                classes="button-row py-1"
            ),

            Label("Output:"),
            TextArea(id="html-entity-output", read_only=True, classes="h-1-3"),

            Static("", id="html-entity-status", classes="mt-1 status-text"),
            classes="p-2"
        )

    @on(Button.Pressed, "#btn-html-entity-encode")
    def on_encode(self) -> None:
        input_widget = self.query_one("#html-entity-input", TextArea)
        output_widget = self.query_one("#html-entity-output", TextArea)
        status_widget = self.query_one("#html-entity-status", Static)

        text = input_widget.text
        if not text:
            status_widget.update("[red]Please enter text to encode.[/red]")
            return

        try:
            encoded = html.escape(text, quote=True)
            output_widget.text = encoded
            status_widget.update("[green]Successfully encoded text to HTML entities.[/green]")
        except Exception as e:
            status_widget.update(f"[red]Error: {str(e)}[/red]")

    @on(Button.Pressed, "#btn-html-entity-decode")
    def on_decode(self) -> None:
        input_widget = self.query_one("#html-entity-input", TextArea)
        output_widget = self.query_one("#html-entity-output", TextArea)
        status_widget = self.query_one("#html-entity-status", Static)

        text = input_widget.text
        if not text:
            status_widget.update("[red]Please enter HTML entities to decode.[/red]")
            return

        try:
            decoded = html.unescape(text)
            output_widget.text = decoded
            status_widget.update("[green]Successfully decoded HTML entities.[/green]")
        except Exception as e:
            status_widget.update(f"[red]Error: {str(e)}[/red]")

    @on(Button.Pressed, "#btn-html-entity-clear")
    def on_clear(self) -> None:
        self.query_one("#html-entity-input", TextArea).text = ""
        self.query_one("#html-entity-output", TextArea).text = ""
        self.query_one("#html-entity-status", Static).update("")
