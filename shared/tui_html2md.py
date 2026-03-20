from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, TextArea
from textual.binding import Binding

from shared.html2md_lab import Html2MdManager


class Html2MdTab(Container):
    """TUI Tab for Html2Md Lab."""

    BINDINGS = [
        Binding("ctrl+r", "convert", "Convert"),
        Binding("ctrl+c", "clear", "Clear"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.manager = Html2MdManager()

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("HTML input:"),
            TextArea(id="input-html", show_line_numbers=True, language="html"),
            Horizontal(
                Button("Convert (Ctrl+R)", id="btn-convert", variant="primary"),
                Button("Clear (Ctrl+C)", id="btn-clear", variant="warning"),
            ),
            Label("Markdown output:"),
            TextArea(id="output-md", show_line_numbers=True, read_only=True, language="markdown"),
            classes="p-2"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-convert":
            self.action_convert()
        elif event.button.id == "btn-clear":
            self.action_clear()

    def action_convert(self) -> None:
        html_input = self.query_one("#input-html", TextArea).text
        if html_input:
            try:
                md_output = self.manager.convert(html_input)
                output_area = self.query_one("#output-md", TextArea)
                output_area.text = md_output
            except Exception as e:
                self.query_one("#output-md", TextArea).text = f"Error converting HTML: {e}"

    def action_clear(self) -> None:
        self.query_one("#input-html", TextArea).text = ""
        self.query_one("#output-md", TextArea).text = ""
