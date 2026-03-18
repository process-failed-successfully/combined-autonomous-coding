from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, TextArea
import base64


class A85LabTab(Container):
    """Tab for Ascii85 Encoding/Decoding."""

    DEFAULT_CSS = """
    A85LabTab {
        layout: vertical;
        height: 100%;
    }

    .a85-box {
        height: auto;
        border: solid $accent;
        padding: 1;
        margin: 1;
    }

    #a85-input, #a85-output {
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Ascii85 Lab (Encoder/Decoder)[/bold]", classes="welcome-text")

            # Input Section
            with Vertical(classes="a85-box"):
                yield Label("Input Text (or Ascii85 to Decode):")
                yield TextArea(id="a85-input", show_line_numbers=False)

            # Controls Section
            with Horizontal(classes="a85-box"):
                yield Button("Encode", id="btn-a85-encode", variant="primary")
                yield Button("Decode", id="btn-a85-decode", variant="success")
                yield Button("Swap Input/Output", id="btn-a85-swap", variant="warning")
                yield Button("Clear", id="btn-a85-clear", variant="error")

            # Output Section
            with Vertical(classes="a85-box"):
                yield Label("Output Text:")
                yield TextArea(id="a85-output", read_only=False, show_line_numbers=False)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-a85-encode":
            self.process(encode=True)
        elif event.button.id == "btn-a85-decode":
            self.process(encode=False)
        elif event.button.id == "btn-a85-swap":
            self.swap_content()
        elif event.button.id == "btn-a85-clear":
            self.clear_content()

    def process(self, encode: bool) -> None:
        text = self.query_one("#a85-input", TextArea).text
        output_area = self.query_one("#a85-output", TextArea)

        if not text:
            self.notify("Input is empty.", severity="warning")
            return

        try:
            if encode:
                result = base64.a85encode(text.encode('utf-8')).decode('utf-8')
            else:
                result = base64.a85decode(text).decode('utf-8')

            output_area.text = result
            self.notify("Done.")
        except Exception as e:
            output_area.text = f"Error: {e}"
            self.notify(f"Exception: {e}", severity="error")

    def swap_content(self) -> None:
        input_area = self.query_one("#a85-input", TextArea)
        output_area = self.query_one("#a85-output", TextArea)

        temp = input_area.text
        input_area.text = output_area.text
        output_area.text = temp
        self.notify("Swapped Input and Output.")

    def clear_content(self) -> None:
        self.query_one("#a85-input", TextArea).text = ""
        self.query_one("#a85-output", TextArea).text = ""
        self.notify("Cleared.")
