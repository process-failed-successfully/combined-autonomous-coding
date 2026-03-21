from textual.app import ComposeResult
from textual.widgets import Label, TextArea
from textual.containers import Vertical, Horizontal
from textual import on
from codecs import encode

class Rot13LabTab(Vertical):
    """Tab for experimenting with ROT13."""

    def compose(self) -> ComposeResult:
        yield Label("[bold]ROT13 Lab[/bold]", classes="welcome-text")

        with Horizontal(classes="stat-box"):
            with Vertical():
                yield Label("Input Text:")
                yield TextArea(id="rot13-input", language=None)
            with Vertical():
                yield Label("ROT13 Output:")
                yield TextArea(id="rot13-output", read_only=True, language=None)

    @on(TextArea.Changed, "#rot13-input")
    def on_input_changed(self, event: TextArea.Changed) -> None:
        input_text = event.text_area.text
        output_area = self.query_one("#rot13-output", TextArea)

        if input_text:
            output_area.text = encode(input_text, "rot_13")
        else:
            output_area.text = ""
