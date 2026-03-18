from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Input, Button, Label
from textual import on

from shared.base91_lab import base91_encode, base91_decode


class Base91LabTab(Container):
    """Tab for Base91 Encoding/Decoding."""

    def compose(self) -> ComposeResult:
        with Container(id="base91-container", classes="lab-container"):
            yield Label("[bold]Base91 Lab (Encoder/Decoder)[/bold]", classes="welcome-text")

            with Horizontal(classes="input-row"):
                yield Label("Input Text (or Base91 to Decode):")
            yield Input(placeholder="Type text here...", id="base91-input")

            with Horizontal(classes="button-row"):
                yield Button("Encode (Text to Base91)", id="btn-base91-encode", variant="primary")
                yield Button("Decode (Base91 to Text)", id="btn-base91-decode", variant="success")

            with Horizontal(classes="input-row"):
                yield Label("Result:")
            yield Input(placeholder="Result will appear here...", id="base91-output", readonly=True)

    @on(Button.Pressed, "#btn-base91-encode")
    def encode_text(self) -> None:
        """Encode the input text."""
        text = self.query_one("#base91-input", Input).value
        try:
            if text:
                result = base91_encode(text.encode('utf-8'))
                self.query_one("#base91-output", Input).value = result
            else:
                self.query_one("#base91-output", Input).value = ""
        except Exception as e:
            self.query_one("#base91-output", Input).value = f"Error: {e}"

    @on(Button.Pressed, "#btn-base91-decode")
    def decode_text(self) -> None:
        """Decode the input text."""
        text = self.query_one("#base91-input", Input).value
        try:
            if text:
                result = base91_decode(text).decode('utf-8')
                self.query_one("#base91-output", Input).value = result
            else:
                self.query_one("#base91-output", Input).value = ""
        except Exception as e:
            self.query_one("#base91-output", Input).value = f"Error: {e}"
