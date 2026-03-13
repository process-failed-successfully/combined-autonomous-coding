from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Input, Button, Label
from shared.base58_lab import b58encode, b58decode

class Base58LabTab(Container):
    """A tab for Base58 encoding and decoding without external dependencies."""

    def compose(self) -> ComposeResult:
        yield Label("Base58 Lab", classes="header-label")
        yield Label("Enter text to encode or decode:")
        yield Input(id="base58-input", placeholder="Enter string here...")

        with Horizontal(classes="button-row"):
            yield Button("Encode Base58", id="btn-encode-base58", variant="primary")
            yield Button("Decode Base58", id="btn-decode-base58", variant="default")

        yield Label("Result:")
        self.output_label = Label("", id="base58-output", classes="output-label")
        yield self.output_label

    def on_button_pressed(self, event: Button.Pressed) -> None:
        input_widget = self.query_one("#base58-input", Input)
        text = input_widget.value

        if not text:
            self.output_label.update("Error: Input cannot be empty.")
            return

        try:
            if event.button.id == "btn-encode-base58":
                result = b58encode(text.encode('utf-8'))
                self.output_label.update(result)
            elif event.button.id == "btn-decode-base58":
                result = b58decode(text).decode('utf-8')
                self.output_label.update(result)
        except Exception as e:
            self.output_label.update(f"Error: {e}")
