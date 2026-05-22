from textual.app import ComposeResult
from textual.widgets import Label, TextArea, Input, Switch
from textual.containers import Vertical, Horizontal
from textual import on
from shared.caesar_lab import caesar_cipher

class CaesarLabTab(Vertical):
    """Tab for experimenting with the Caesar cipher."""

    def compose(self) -> ComposeResult:
        yield Label("[bold]Caesar Lab[/bold]", classes="welcome-text")

        with Horizontal(classes="stat-box"):
            with Vertical():
                yield Label("Input Text:")
                yield TextArea(id="caesar-input", language=None)
                with Horizontal():
                    yield Label("Shift:", classes="label-inline")
                    yield Input(value="13", type="integer", id="caesar-shift", classes="input-inline")
                with Horizontal():
                    yield Label("Decode:", classes="label-inline")
                    yield Switch(id="caesar-decode", value=False)
            with Vertical():
                yield Label("Caesar Output:")
                yield TextArea(id="caesar-output", disabled=True, language=None)

    @on(TextArea.Changed, "#caesar-input")
    @on(Input.Changed, "#caesar-shift")
    @on(Switch.Changed, "#caesar-decode")
    def on_input_changed(self) -> None:
        input_text = self.query_one("#caesar-input", TextArea).text
        shift_str = self.query_one("#caesar-shift", Input).value
        decode = self.query_one("#caesar-decode", Switch).value
        output_area = self.query_one("#caesar-output", TextArea)

        if not input_text:
            output_area.text = ""
            return

        try:
            shift = int(shift_str) if shift_str else 0
        except ValueError:
            output_area.text = "Error: Invalid shift value."
            return

        output_area.text = caesar_cipher(input_text, shift, decode=decode)
