from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Checkbox, Label, TextArea
import base64


class Base32LabTab(Container):
    """Tab for Base32 Encoding/Decoding."""

    DEFAULT_CSS = """
    Base32LabTab {
        layout: vertical;
        height: 100%;
    }

    .b32-box {
        height: auto;
        border: solid $accent;
        padding: 1;
        margin: 1;
    }

    #b32-input, #b32-output {
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Base32 Lab (Encoder/Decoder)[/bold]", classes="welcome-text")

            # Input Section
            with Vertical(classes="b32-box"):
                yield Label("Input Text (or Base32 to Decode):")
                yield TextArea(id="b32-input", show_line_numbers=False)

            # Controls Section
            with Horizontal(classes="b32-box"):
                yield Button("Encode", id="btn-b32-encode", variant="primary")
                yield Button("Decode", id="btn-b32-decode", variant="success")
                yield Button("Swap Input/Output", id="btn-b32-swap", variant="warning")
                yield Button("Clear", id="btn-b32-clear", variant="error")
                yield Checkbox("Use Base32Hex", id="cb-b32-hex")

            # Output Section
            with Vertical(classes="b32-box"):
                yield Label("Output Text:")
                yield TextArea(id="b32-output", read_only=False, show_line_numbers=False)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-b32-encode":
            self.process(encode=True)
        elif event.button.id == "btn-b32-decode":
            self.process(encode=False)
        elif event.button.id == "btn-b32-swap":
            self.swap_content()
        elif event.button.id == "btn-b32-clear":
            self.clear_content()

    def process(self, encode: bool) -> None:
        text = self.query_one("#b32-input", TextArea).text
        output_area = self.query_one("#b32-output", TextArea)
        use_hex = self.query_one("#cb-b32-hex", Checkbox).value

        if not text:
            self.notify("Input is empty.", severity="warning")
            return

        try:
            if encode:
                if use_hex:
                    result = base64.b32hexencode(text.encode('utf-8')).decode('utf-8')
                else:
                    result = base64.b32encode(text.encode('utf-8')).decode('utf-8')
            else:
                if use_hex:
                    result = base64.b32hexdecode(text, casefold=True).decode('utf-8')
                else:
                    result = base64.b32decode(text, casefold=True).decode('utf-8')

            output_area.text = result
            self.notify("Done.")
        except Exception as e:
            output_area.text = f"Error: {e}"
            self.notify(f"Exception: {e}", severity="error")

    def swap_content(self) -> None:
        input_area = self.query_one("#b32-input", TextArea)
        output_area = self.query_one("#b32-output", TextArea)

        temp = input_area.text
        input_area.text = output_area.text
        output_area.text = temp
        self.notify("Swapped Input and Output.")

    def clear_content(self) -> None:
        self.query_one("#b32-input", TextArea).text = ""
        self.query_one("#b32-output", TextArea).text = ""
        self.notify("Cleared.")
