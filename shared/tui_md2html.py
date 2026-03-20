from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, TextArea, Button
from textual.binding import Binding

from shared.md2html_lab import Md2HtmlManager

class Md2HtmlTab(Container):
    """TUI Tab for Md2Html Lab."""

    BINDINGS = [
        Binding("ctrl+r", "convert", "Convert"),
        Binding("ctrl+c", "clear", "Clear"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.manager = Md2HtmlManager()

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("Markdown input:"),
            TextArea(id="input-md", show_line_numbers=True, language="markdown"),
            Horizontal(
                Button("Convert (Ctrl+R)", id="btn-convert", variant="primary"),
                Button("Clear (Ctrl+C)", id="btn-clear", variant="warning"),
            ),
            Label("HTML output:"),
            TextArea(id="output-html", show_line_numbers=True, read_only=True, language="html"),
            classes="p-2"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-convert":
            self.action_convert()
        elif event.button.id == "btn-clear":
            self.action_clear()

    def action_convert(self) -> None:
        md_input = self.query_one("#input-md", TextArea).text
        if md_input:
            try:
                html_output = self.manager.convert(md_input)
                output_area = self.query_one("#output-html", TextArea)
                output_area.text = html_output
            except Exception as e:
                self.query_one("#output-html", TextArea).text = f"Error converting Markdown: {e}"

    def action_clear(self) -> None:
        self.query_one("#input-md", TextArea).text = ""
        self.query_one("#output-html", TextArea).text = ""
