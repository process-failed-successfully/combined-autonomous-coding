from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, TextArea
from shared.devtools import DevTools


class Base64UrlLabTab(Container):
    """Tab for Base64URL Encoding/Decoding."""

    DEFAULT_CSS = """
    Base64UrlLabTab {
        layout: vertical;
        height: 100%;
    }

    .b64url-box {
        height: auto;
        border: solid $accent;
        padding: 1;
        margin: 1;
    }

    #b64url-input, #b64url-output {
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Base64URL Lab (Encoder/Decoder)[/bold]", classes="welcome-text")

            # Input Section
            with Vertical(classes="b64url-box"):
                yield Label("Input Text (or Base64URL to Decode):")
                yield TextArea(id="b64url-input", show_line_numbers=False)

            # Controls Section
            with Horizontal(classes="b64url-box"):
                yield Button("Encode", id="btn-b64url-encode", variant="primary")
                yield Button("Decode", id="btn-b64url-decode", variant="success")
                yield Button("Swap Input/Output", id="btn-b64url-swap", variant="warning")
                yield Button("Clear", id="btn-b64url-clear", variant="error")

            # Output Section
            with Vertical(classes="b64url-box"):
                yield Label("Output Text:")
                yield TextArea(id="b64url-output", read_only=False, show_line_numbers=False)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-b64url-encode":
            self.process(encode=True)
        elif event.button.id == "btn-b64url-decode":
            self.process(encode=False)
        elif event.button.id == "btn-b64url-swap":
            self.swap_content()
        elif event.button.id == "btn-b64url-clear":
            self.clear_content()

    def process(self, encode: bool) -> None:
        text = self.query_one("#b64url-input", TextArea).text
        output_area = self.query_one("#b64url-output", TextArea)

        if not text:
            self.notify("Input is empty.", severity="warning")
            return

        try:
            if encode:
                result = DevTools.base64url_encode(text)
            else:
                result = DevTools.base64url_decode(text)

            output_area.text = result

            if result.startswith("Error"):
                self.notify("Operation failed.", severity="error")
            else:
                self.notify("Done.")

        except Exception as e:
            output_area.text = f"Error: {e}"
            self.notify(f"Exception: {e}", severity="error")

    def swap_content(self) -> None:
        input_area = self.query_one("#b64url-input", TextArea)
        output_area = self.query_one("#b64url-output", TextArea)

        temp = input_area.text
        input_area.text = output_area.text
        output_area.text = temp
        self.notify("Swapped Input and Output.")

    def clear_content(self) -> None:
        self.query_one("#b64url-input", TextArea).text = ""
        self.query_one("#b64url-output", TextArea).text = ""
        self.notify("Cleared.")
