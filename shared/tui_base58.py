from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, TextArea
from shared.base58_lab import b58encode, b58decode


class Base58LabTab(Container):
    """Tab for Base58 Encoding/Decoding."""

    DEFAULT_CSS = """
    Base58LabTab {
        layout: vertical;
        height: 100%;
    }

    .b58-box {
        height: auto;
        border: solid $accent;
        padding: 1;
        margin: 1;
    }

    #b58-input, #b58-output {
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Base58 Lab (Encoder/Decoder)[/bold]", classes="welcome-text")

            # Input Section
            with Vertical(classes="b58-box"):
                yield Label("Input Text (or Base58 to Decode):")
                yield TextArea(id="b58-input", show_line_numbers=False)

            # Controls Section
            with Horizontal(classes="b58-box"):
                yield Button("Encode", id="btn-b58-encode", variant="primary")
                yield Button("Decode", id="btn-b58-decode", variant="success")
                yield Button("Swap Input/Output", id="btn-b58-swap", variant="warning")
                yield Button("Clear", id="btn-b58-clear", variant="error")

            # Output Section
            with Vertical(classes="b58-box"):
                yield Label("Output Text:")
                yield TextArea(id="b58-output", read_only=False, show_line_numbers=False)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-b58-encode":
            self.process(encode=True)
        elif event.button.id == "btn-b58-decode":
            self.process(encode=False)
        elif event.button.id == "btn-b58-swap":
            self.swap_content()
        elif event.button.id == "btn-b58-clear":
            self.clear_content()

    def process(self, encode: bool) -> None:
        text = self.query_one("#b58-input", TextArea).text
        output_area = self.query_one("#b58-output", TextArea)

        if not text:
            self.notify("Input is empty.", severity="warning")
            return

        try:
            if encode:
                result = b58encode(text.encode('utf-8'))
            else:
                result = b58decode(text).decode('utf-8')

            output_area.text = result
            self.notify("Done.")
        except Exception as e:
            output_area.text = f"Error: {e}"
            self.notify(f"Exception: {e}", severity="error")

    def swap_content(self) -> None:
        input_area = self.query_one("#b58-input", TextArea)
        output_area = self.query_one("#b58-output", TextArea)

        temp = input_area.text
        input_area.text = output_area.text
        output_area.text = temp
        self.notify("Swapped Input and Output.")

    def clear_content(self) -> None:
        self.query_one("#b58-input", TextArea).text = ""
        self.query_one("#b58-output", TextArea).text = ""
        self.notify("Cleared.")
