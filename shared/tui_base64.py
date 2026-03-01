from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, TextArea
from shared.devtools import DevTools


class Base64LabTab(Container):
    """Tab for Base64 Encoding/Decoding."""

    DEFAULT_CSS = """
    Base64LabTab {
        layout: vertical;
        height: 100%;
    }

    .b64-box {
        height: auto;
        border: solid $accent;
        padding: 1;
        margin: 1;
    }

    #b64-input, #b64-output {
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Base64 Lab (Encoder/Decoder)[/bold]", classes="welcome-text")

            # Input Section
            with Vertical(classes="b64-box"):
                yield Label("Input Text (or Base64 to Decode):")
                yield TextArea(id="b64-input", show_line_numbers=False)

            # Controls Section
            with Horizontal(classes="b64-box"):
                yield Button("Encode", id="btn-b64-encode", variant="primary")
                yield Button("Decode", id="btn-b64-decode", variant="success")
                yield Button("Swap Input/Output", id="btn-b64-swap", variant="warning")
                yield Button("Clear", id="btn-b64-clear", variant="error")

            # Output Section
            with Vertical(classes="b64-box"):
                yield Label("Output Text:")
                yield TextArea(id="b64-output", read_only=False, show_line_numbers=False)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-b64-encode":
            self.process(encode=True)
        elif event.button.id == "btn-b64-decode":
            self.process(encode=False)
        elif event.button.id == "btn-b64-swap":
            self.swap_content()
        elif event.button.id == "btn-b64-clear":
            self.clear_content()

    def process(self, encode: bool) -> None:
        text = self.query_one("#b64-input", TextArea).text
        output_area = self.query_one("#b64-output", TextArea)

        if not text:
            self.notify("Input is empty.", severity="warning")
            return

        try:
            if encode:
                result = DevTools.base64_encode(text)
            else:
                result = DevTools.base64_decode(text)

            output_area.text = result

            if result.startswith("Error:"):
                self.notify("Operation failed.", severity="error")
            else:
                self.notify("Done.")

        except Exception as e:
            output_area.text = f"Error: {e}"
            self.notify(f"Exception: {e}", severity="error")

    def swap_content(self) -> None:
        input_area = self.query_one("#b64-input", TextArea)
        output_area = self.query_one("#b64-output", TextArea)

        temp = input_area.text
        input_area.text = output_area.text
        output_area.text = temp
        self.notify("Swapped Input and Output.")

    def clear_content(self) -> None:
        self.query_one("#b64-input", TextArea).text = ""
        self.query_one("#b64-output", TextArea).text = ""
        self.notify("Cleared.")
