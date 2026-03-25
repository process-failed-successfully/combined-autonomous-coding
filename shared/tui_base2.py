from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, TextArea
from shared.base2_lab import encode_base2, decode_base2


class Base2LabTab(Container):
    """Tab for Base2 Encoding/Decoding."""

    DEFAULT_CSS = """
    Base2LabTab {
        layout: vertical;
        height: 100%;
    }

    .b2-box {
        height: auto;
        border: solid $accent;
        padding: 1;
        margin: 1;
    }

    #b2-input, #b2-output {
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Base2 Lab (Binary Encoder/Decoder)[/bold]", classes="welcome-text")

            # Input Section
            with Vertical(classes="b2-box"):
                yield Label("Input Text (or Binary to Decode):")
                yield TextArea(id="b2-input", show_line_numbers=False)

            # Controls Section
            with Horizontal(classes="b2-box"):
                yield Button("Encode", id="btn-b2-encode", variant="primary")
                yield Button("Decode", id="btn-b2-decode", variant="success")
                yield Button("Swap Input/Output", id="btn-b2-swap", variant="warning")
                yield Button("Clear", id="btn-b2-clear", variant="error")

            # Output Section
            with Vertical(classes="b2-box"):
                yield Label("Output Text:")
                yield TextArea(id="b2-output", read_only=False, show_line_numbers=False)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-b2-encode":
            self.process(encode=True)
        elif event.button.id == "btn-b2-decode":
            self.process(encode=False)
        elif event.button.id == "btn-b2-swap":
            self.swap_content()
        elif event.button.id == "btn-b2-clear":
            self.clear_content()

    def process(self, encode: bool) -> None:
        text = self.query_one("#b2-input", TextArea).text
        output_area = self.query_one("#b2-output", TextArea)

        if not text:
            self.notify("Input is empty.", severity="warning")
            return

        try:
            if encode:
                result = encode_base2(text)
            else:
                result = decode_base2(text)

            output_area.text = result
            self.notify("Done.")
        except Exception as e:
            output_area.text = f"Error: {e}"
            self.notify(f"Exception: {e}", severity="error")

    def swap_content(self) -> None:
        input_area = self.query_one("#b2-input", TextArea)
        output_area = self.query_one("#b2-output", TextArea)

        temp = input_area.text
        input_area.text = output_area.text
        output_area.text = temp
        self.notify("Swapped Input and Output.")

    def clear_content(self) -> None:
        self.query_one("#b2-input", TextArea).text = ""
        self.query_one("#b2-output", TextArea).text = ""
        self.notify("Cleared.")
