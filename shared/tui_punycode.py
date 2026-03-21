from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, TextArea
import idna


class PunycodeLabTab(Container):
    """Tab for Punycode Encoding/Decoding."""

    DEFAULT_CSS = """
    PunycodeLabTab {
        layout: vertical;
        height: 100%;
    }

    .punycode-box {
        height: auto;
        border: solid $accent;
        padding: 1;
        margin: 1;
    }

    #punycode-input, #punycode-output {
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Punycode Lab (IDNA Encoder/Decoder)[/bold]", classes="welcome-text")

            # Input Section
            with Vertical(classes="punycode-box"):
                yield Label("Input Text (or Punycode to Decode):")
                yield TextArea(id="punycode-input", show_line_numbers=False)

            # Controls Section
            with Horizontal(classes="punycode-box"):
                yield Button("Encode", id="btn-punycode-encode", variant="primary")
                yield Button("Decode", id="btn-punycode-decode", variant="success")
                yield Button("Swap Input/Output", id="btn-punycode-swap", variant="warning")
                yield Button("Clear", id="btn-punycode-clear", variant="error")

            # Output Section
            with Vertical(classes="punycode-box"):
                yield Label("Output Text:")
                yield TextArea(id="punycode-output", read_only=False, show_line_numbers=False)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-punycode-encode":
            self.process(encode=True)
        elif event.button.id == "btn-punycode-decode":
            self.process(encode=False)
        elif event.button.id == "btn-punycode-swap":
            self.swap_content()
        elif event.button.id == "btn-punycode-clear":
            self.clear_content()

    def process(self, encode: bool) -> None:
        text = self.query_one("#punycode-input", TextArea).text.strip()
        output_area = self.query_one("#punycode-output", TextArea)

        if not text:
            self.notify("Input is empty.", severity="warning")
            return

        try:
            if encode:
                result = idna.encode(text).decode('utf-8')
            else:
                result = idna.decode(text)

            output_area.text = result
            self.notify("Done.")

        except Exception as e:
            output_area.text = f"Error: {e}"
            self.notify(f"Exception: {e}", severity="error")

    def swap_content(self) -> None:
        input_area = self.query_one("#punycode-input", TextArea)
        output_area = self.query_one("#punycode-output", TextArea)

        temp = input_area.text
        input_area.text = output_area.text
        output_area.text = temp
        self.notify("Swapped Input and Output.")

    def clear_content(self) -> None:
        self.query_one("#punycode-input", TextArea).text = ""
        self.query_one("#punycode-output", TextArea).text = ""
        self.notify("Cleared.")
