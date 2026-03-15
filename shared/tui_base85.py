from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, TextArea
import base64

class Base85LabTab(Container):
    """Tab for Base85 Encoding/Decoding."""

    DEFAULT_CSS = """
    Base85LabTab {
        layout: vertical;
        height: 100%;
    }

    .b85-box {
        height: auto;
        border: solid $accent;
        padding: 1;
        margin: 1;
    }

    #b85-input, #b85-output {
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Base85 Lab (Encoder/Decoder)[/bold]", classes="welcome-text")

            # Input Section
            with Vertical(classes="b85-box"):
                yield Label("Input Text (or Base85 to Decode):")
                yield TextArea(id="b85-input", show_line_numbers=False)

            # Controls Section
            with Horizontal(classes="b85-box"):
                yield Button("Encode", id="btn-b85-encode", variant="primary")
                yield Button("Decode", id="btn-b85-decode", variant="success")
                yield Button("Swap Input/Output", id="btn-b85-swap", variant="warning")
                yield Button("Clear", id="btn-b85-clear", variant="error")

            # Output Section
            with Vertical(classes="b85-box"):
                yield Label("Output Text:")
                yield TextArea(id="b85-output", read_only=False, show_line_numbers=False)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-b85-encode":
            self.process(encode=True)
        elif event.button.id == "btn-b85-decode":
            self.process(encode=False)
        elif event.button.id == "btn-b85-swap":
            self.swap_content()
        elif event.button.id == "btn-b85-clear":
            self.clear_content()

    def process(self, encode: bool) -> None:
        text = self.query_one("#b85-input", TextArea).text
        output_area = self.query_one("#b85-output", TextArea)

        if not text:
            self.notify("Input is empty.", severity="warning")
            return

        try:
            if encode:
                result = base64.b85encode(text.encode('utf-8')).decode('utf-8')
            else:
                result = base64.b85decode(text).decode('utf-8')

            output_area.text = result
            self.notify("Done.")
        except Exception as e:
            output_area.text = f"Error: {e}"
            self.notify(f"Exception: {e}", severity="error")

    def swap_content(self) -> None:
        input_area = self.query_one("#b85-input", TextArea)
        output_area = self.query_one("#b85-output", TextArea)

        temp = input_area.text
        input_area.text = output_area.text
        output_area.text = temp
        self.notify("Swapped Input and Output.")

    def clear_content(self) -> None:
        self.query_one("#b85-input", TextArea).text = ""
        self.query_one("#b85-output", TextArea).text = ""
        self.notify("Cleared.")
