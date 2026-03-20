from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, TextArea
from shared.base45_lab import b45encode, b45decode


class Base45LabTab(Container):
    """Tab for Base45 Encoding/Decoding."""

    DEFAULT_CSS = """
    Base45LabTab {
        layout: vertical;
        height: 100%;
    }

    .b45-box {
        height: auto;
        border: solid $accent;
        padding: 1;
        margin: 1;
    }

    #b45-input, #b45-output {
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Base45 Lab (Encoder/Decoder)[/bold]", classes="welcome-text")

            # Input Section
            with Vertical(classes="b45-box"):
                yield Label("Input Text (or Base45 to Decode):")
                yield TextArea(id="b45-input", show_line_numbers=False)

            # Controls Section
            with Horizontal(classes="b45-box"):
                yield Button("Encode", id="btn-b45-encode", variant="primary")
                yield Button("Decode", id="btn-b45-decode", variant="success")
                yield Button("Swap Input/Output", id="btn-b45-swap", variant="warning")
                yield Button("Clear", id="btn-b45-clear", variant="error")

            # Output Section
            with Vertical(classes="b45-box"):
                yield Label("Output Text:")
                yield TextArea(id="b45-output", read_only=False, show_line_numbers=False)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-b45-encode":
            self.process(encode=True)
        elif event.button.id == "btn-b45-decode":
            self.process(encode=False)
        elif event.button.id == "btn-b45-swap":
            self.swap_content()
        elif event.button.id == "btn-b45-clear":
            self.clear_content()

    def process(self, encode: bool) -> None:
        text = self.query_one("#b45-input", TextArea).text
        output_area = self.query_one("#b45-output", TextArea)

        if not text:
            self.notify("Input is empty.", severity="warning")
            return

        try:
            if encode:
                result = b45encode(text.encode('utf-8'))
            else:
                result = b45decode(text).decode('utf-8')

            output_area.text = result
            self.notify("Done.")
        except Exception as e:
            output_area.text = f"Error: {e}"
            self.notify(f"Exception: {e}", severity="error")

    def swap_content(self) -> None:
        input_area = self.query_one("#b45-input", TextArea)
        output_area = self.query_one("#b45-output", TextArea)

        temp = input_area.text
        input_area.text = output_area.text
        output_area.text = temp
        self.notify("Swapped Input and Output.")

    def clear_content(self) -> None:
        self.query_one("#b45-input", TextArea).text = ""
        self.query_one("#b45-output", TextArea).text = ""
        self.notify("Cleared.")
