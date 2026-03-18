from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, TextArea
from shared.base91_lab import base91_encode, base91_decode


class Base91LabTab(Container):
    """Tab for Base91 Encoding/Decoding."""

    DEFAULT_CSS = """
    Base91LabTab {
        layout: vertical;
        height: 100%;
    }

    .b91-box {
        height: auto;
        border: solid $accent;
        padding: 1;
        margin: 1;
    }

    #b91-input, #b91-output {
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Base91 Lab (Encoder/Decoder)[/bold]", classes="welcome-text")

            # Input Section
            with Vertical(classes="b91-box"):
                yield Label("Input Text (or Base91 to Decode):")
                yield TextArea(id="b91-input", show_line_numbers=False)

            # Controls Section
            with Horizontal(classes="b91-box"):
                yield Button("Encode", id="btn-b91-encode", variant="primary")
                yield Button("Decode", id="btn-b91-decode", variant="success")
                yield Button("Swap Input/Output", id="btn-b91-swap", variant="warning")
                yield Button("Clear", id="btn-b91-clear", variant="error")

            # Output Section
            with Vertical(classes="b91-box"):
                yield Label("Output Text:")
                yield TextArea(id="b91-output", read_only=False, show_line_numbers=False)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-b91-encode":
            self.process(encode=True)
        elif event.button.id == "btn-b91-decode":
            self.process(encode=False)
        elif event.button.id == "btn-b91-swap":
            self.swap_content()
        elif event.button.id == "btn-b91-clear":
            self.clear_content()

    def process(self, encode: bool) -> None:
        text = self.query_one("#b91-input", TextArea).text
        output_area = self.query_one("#b91-output", TextArea)

        if not text:
            self.notify("Input is empty.", severity="warning")
            return

        try:
            if encode:
                result = base91_encode(text.encode('utf-8'))
            else:
                result = base91_decode(text).decode('utf-8')

            output_area.text = result
            self.notify("Done.")

        except Exception as e:
            output_area.text = f"Error: {e}"
            self.notify(f"Exception: {e}", severity="error")

    def swap_content(self) -> None:
        input_area = self.query_one("#b91-input", TextArea)
        output_area = self.query_one("#b91-output", TextArea)

        temp = input_area.text
        input_area.text = output_area.text
        output_area.text = temp
        self.notify("Swapped Input and Output.")

    def clear_content(self) -> None:
        self.query_one("#b91-input", TextArea).text = ""
        self.query_one("#b91-output", TextArea).text = ""
        self.notify("Cleared.")
