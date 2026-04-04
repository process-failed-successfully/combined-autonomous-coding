from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, TextArea, Button
from textual import on

from shared.regex_escape_lab import RegexEscapeManager


class RegexEscapeLabTab(Container):
    """Tab for Regex Escape Lab."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = RegexEscapeManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Regex Escape Lab[/bold]", classes="welcome-text")

            with Horizontal(classes="stat-box"):
                yield Button("Escape", id="btn-regex-escape", variant="primary")
                yield Button("Unescape", id="btn-regex-unescape", variant="warning")
                yield Button("Clear", id="btn-regex-clear", variant="default")

            with Horizontal():
                with Vertical(classes="stat-box"):
                    yield Label("[bold]Input[/bold]")
                    yield TextArea(id="regex-escape-input")

                with Vertical(classes="stat-box"):
                    yield Label("[bold]Output[/bold]")
                    yield TextArea(id="regex-escape-output", read_only=True)

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        input_area = self.query_one("#regex-escape-input", TextArea)
        output_area = self.query_one("#regex-escape-output", TextArea)
        text = input_area.text

        if event.button.id == "btn-regex-escape":
            if not text:
                self.notify("Input required.", severity="error")
                return
            output_area.text = self.manager.escape(text)
            self.notify("Text escaped.")

        elif event.button.id == "btn-regex-unescape":
            if not text:
                self.notify("Input required.", severity="error")
                return
            output_area.text = self.manager.unescape(text)
            self.notify("Text unescaped.")

        elif event.button.id == "btn-regex-clear":
            input_area.text = ""
            output_area.text = ""
            self.notify("Cleared.")
