from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, TextArea
import urllib.parse


class UrlEncodeLabTab(Container):
    """Tab for URL Encoding/Decoding."""

    DEFAULT_CSS = """
    UrlEncodeLabTab {
        layout: vertical;
        height: 100%;
    }

    .urlencode-box {
        height: auto;
        border: solid $accent;
        padding: 1;
        margin: 1;
    }

    #urlencode-input, #urlencode-output {
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]URL Encode Lab (Encoder/Decoder)[/bold]", classes="welcome-text")

            # Input Section
            with Vertical(classes="urlencode-box"):
                yield Label("Input Text (or URL to Decode):")
                yield TextArea(id="urlencode-input", show_line_numbers=False)

            # Controls Section
            with Horizontal(classes="urlencode-box"):
                yield Button("Encode", id="btn-urlencode-encode", variant="primary")
                yield Button("Decode", id="btn-urlencode-decode", variant="success")
                yield Button("Swap Input/Output", id="btn-urlencode-swap", variant="warning")
                yield Button("Clear", id="btn-urlencode-clear", variant="error")

            # Output Section
            with Vertical(classes="urlencode-box"):
                yield Label("Output Text:")
                yield TextArea(id="urlencode-output", read_only=False, show_line_numbers=False)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-urlencode-encode":
            self.process(encode=True)
        elif event.button.id == "btn-urlencode-decode":
            self.process(encode=False)
        elif event.button.id == "btn-urlencode-swap":
            self.swap_content()
        elif event.button.id == "btn-urlencode-clear":
            self.clear_content()

    def process(self, encode: bool) -> None:
        input_area = self.query_one("#urlencode-input", TextArea)
        output_area = self.query_one("#urlencode-output", TextArea)

        text = input_area.text

        if not text:
            self.notify("Input is empty.", severity="warning")
            return

        try:
            if encode:
                result = urllib.parse.quote(text)
            else:
                result = urllib.parse.unquote(text)

            output_area.text = result
            self.notify("Done.")
        except Exception as e:
            output_area.text = f"Error: {e}"
            self.notify(f"Exception: {e}", severity="error")

    def swap_content(self) -> None:
        input_area = self.query_one("#urlencode-input", TextArea)
        output_area = self.query_one("#urlencode-output", TextArea)

        temp = input_area.text
        input_area.text = output_area.text
        output_area.text = temp
        self.notify("Swapped Input and Output.")

    def clear_content(self) -> None:
        self.query_one("#urlencode-input", TextArea).text = ""
        self.query_one("#urlencode-output", TextArea).text = ""
        self.notify("Cleared.")
