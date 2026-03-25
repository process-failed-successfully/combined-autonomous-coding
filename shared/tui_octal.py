from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, TextArea

from shared.octal_lab import octal_encode, octal_decode


class OctalLabTab(Container):
    """Tab for Octal Encoding/Decoding."""

    DEFAULT_CSS = """
    OctalLabTab {
        layout: vertical;
        height: 100%;
    }

    .octal-box {
        height: auto;
        border: solid $accent;
        padding: 1;
        margin: 1;
    }

    #octal-input, #octal-output {
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Octal Lab (Encoder/Decoder)[/bold]", classes="welcome-text")

            # Input Section
            with Vertical(classes="octal-box"):
                yield Label("Input Text (or Octal to Decode):")
                yield TextArea(id="octal-input", show_line_numbers=False)

            # Controls Section
            with Horizontal(classes="octal-box"):
                yield Button("Encode", id="btn-octal-encode", variant="primary")
                yield Button("Decode", id="btn-octal-decode", variant="success")
                yield Button("Swap Input/Output", id="btn-octal-swap", variant="warning")
                yield Button("Clear", id="btn-octal-clear", variant="error")

            # Output Section
            with Vertical(classes="octal-box"):
                yield Label("Output Text:")
                yield TextArea(id="octal-output", read_only=False, show_line_numbers=False)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-octal-encode":
            self.process(encode=True)
        elif event.button.id == "btn-octal-decode":
            self.process(encode=False)
        elif event.button.id == "btn-octal-swap":
            self.swap_content()
        elif event.button.id == "btn-octal-clear":
            self.clear_content()

    def process(self, encode: bool) -> None:
        text = self.query_one("#octal-input", TextArea).text
        output_area = self.query_one("#octal-output", TextArea)

        if not text:
            self.notify("Input is empty.", severity="warning")
            return

        try:
            if encode:
                result = octal_encode(text.encode('utf-8'))
            else:
                result = octal_decode(text).decode('utf-8')

            output_area.text = result
            self.notify("Done.")

        except Exception as e:
            output_area.text = f"Error: {e}"
            self.notify(f"Exception: {e}", severity="error")

    def swap_content(self) -> None:
        input_area = self.query_one("#octal-input", TextArea)
        output_area = self.query_one("#octal-output", TextArea)

        temp = input_area.text
        input_area.text = output_area.text
        output_area.text = temp
        self.notify("Swapped Input and Output.")

    def clear_content(self) -> None:
        self.query_one("#octal-input", TextArea).text = ""
        self.query_one("#octal-output", TextArea).text = ""
        self.notify("Cleared.")
