from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, TextArea

from shared.binary_lab import text_to_binary, binary_to_text


class BinaryLabTab(Container):
    """Tab for Binary Encoding/Decoding."""

    DEFAULT_CSS = """
    BinaryLabTab {
        layout: vertical;
        height: 100%;
    }

    .binary-box {
        height: auto;
        border: solid $accent;
        padding: 1;
        margin: 1;
    }

    #binary-input, #binary-output {
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Binary Lab (Encoder/Decoder)[/bold]", classes="welcome-text")

            # Input Section
            with Vertical(classes="binary-box"):
                yield Label("Input Text (or Binary to Decode):")
                yield TextArea(id="binary-input", show_line_numbers=False)

            # Controls Section
            with Horizontal(classes="binary-box"):
                yield Button("Encode", id="btn-binary-encode", variant="primary")
                yield Button("Decode", id="btn-binary-decode", variant="success")
                yield Button("Swap Input/Output", id="btn-binary-swap", variant="warning")
                yield Button("Clear", id="btn-binary-clear", variant="error")

            # Output Section
            with Vertical(classes="binary-box"):
                yield Label("Output Text:")
                yield TextArea(id="binary-output", read_only=False, show_line_numbers=False)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-binary-encode":
            self.process(encode=True)
        elif event.button.id == "btn-binary-decode":
            self.process(encode=False)
        elif event.button.id == "btn-binary-swap":
            self.swap_content()
        elif event.button.id == "btn-binary-clear":
            self.clear_content()

    def process(self, encode: bool) -> None:
        input_area = self.query_one("#binary-input", TextArea)
        output_area = self.query_one("#binary-output", TextArea)
        text = input_area.text

        if not text:
            self.notify("Input is empty.", severity="warning")
            return

        try:
            if encode:
                result = text_to_binary(text)
            else:
                result = binary_to_text(text)

            output_area.text = result
            self.notify("Done.")
        except Exception as e:
            output_area.text = f"Error: {e}"
            self.notify(f"Exception: {e}", severity="error")

    def swap_content(self) -> None:
        input_area = self.query_one("#binary-input", TextArea)
        output_area = self.query_one("#binary-output", TextArea)

        temp = input_area.text
        input_area.text = output_area.text
        output_area.text = temp
        self.notify("Swapped Input and Output.")

    def clear_content(self) -> None:
        self.query_one("#binary-input", TextArea).text = ""
        self.query_one("#binary-output", TextArea).text = ""
        self.notify("Cleared.")
