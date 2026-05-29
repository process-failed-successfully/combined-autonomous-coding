from textual.app import ComposeResult
from textual.widgets import Label, TextArea, Input, Switch
from textual.containers import Vertical, Horizontal
from textual import on
from shared.vigenere_lab import vigenere_cipher


class VigenereLabTab(Vertical):
    """Tab for experimenting with the Vigenère cipher."""

    def compose(self) -> ComposeResult:
        yield Label("[bold]Vigenère Lab[/bold]", classes="welcome-text")

        with Horizontal(classes="stat-box"):
            with Vertical():
                yield Label("Input Text:")
                yield TextArea(id="vigenere-input", language=None)
                with Horizontal():
                    yield Label("Key:", classes="label-inline")
                    yield Input(value="", id="vigenere-key", classes="input-inline")
                with Horizontal():
                    yield Label("Decode:", classes="label-inline")
                    yield Switch(id="vigenere-decode", value=False)
            with Vertical():
                yield Label("Vigenère Output:")
                yield TextArea(id="vigenere-output", disabled=True, language=None)

    @on(TextArea.Changed, "#vigenere-input")
    @on(Input.Changed, "#vigenere-key")
    @on(Switch.Changed, "#vigenere-decode")
    def on_input_changed(self) -> None:
        input_text = self.query_one("#vigenere-input", TextArea).text
        key = self.query_one("#vigenere-key", Input).value
        decode = self.query_one("#vigenere-decode", Switch).value
        output_area = self.query_one("#vigenere-output", TextArea)

        if not input_text:
            output_area.text = ""
            return

        if not key:
            output_area.text = input_text
            return

        output_area.text = vigenere_cipher(input_text, key, decode=decode)
