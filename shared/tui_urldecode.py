from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, TextArea
import urllib.parse


class UrlDecodeLabTab(Container):
    """Tab for URL Decoding."""

    DEFAULT_CSS = """
    UrlDecodeLabTab {
        layout: vertical;
        height: 100%;
    }

    .urldecode-box {
        height: auto;
        border: solid $accent;
        padding: 1;
        margin: 1;
    }

    #urldecode-input, #urldecode-output {
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]URL Decode Lab[/bold]", classes="welcome-text")

            # Input Section
            with Vertical(classes="urldecode-box"):
                yield Label("Input URL/Text to Decode:")
                yield TextArea(id="urldecode-input", show_line_numbers=False)

            # Controls Section
            with Horizontal(classes="urldecode-box"):
                yield Button("Decode", id="btn-urldecode-decode", variant="primary")
                yield Button("Swap Input/Output", id="btn-urldecode-swap", variant="warning")
                yield Button("Clear", id="btn-urldecode-clear", variant="error")

            # Output Section
            with Vertical(classes="urldecode-box"):
                yield Label("Output Decoded Text:")
                yield TextArea(id="urldecode-output", read_only=False, show_line_numbers=False)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-urldecode-decode":
            self.process()
        elif event.button.id == "btn-urldecode-swap":
            self.swap_content()
        elif event.button.id == "btn-urldecode-clear":
            self.clear_content()

    def process(self) -> None:
        input_area = self.query_one("#urldecode-input", TextArea)
        output_area = self.query_one("#urldecode-output", TextArea)

        text = input_area.text

        if not text:
            self.notify("Input is empty.", severity="warning")
            return

        try:
            result = urllib.parse.unquote(text)
            output_area.text = result
            self.notify("Done.")
        except Exception as e:
            output_area.text = f"Error: {e}"
            self.notify(f"Exception: {e}", severity="error")

    def swap_content(self) -> None:
        input_area = self.query_one("#urldecode-input", TextArea)
        output_area = self.query_one("#urldecode-output", TextArea)

        temp = input_area.text
        input_area.text = output_area.text
        output_area.text = temp
        self.notify("Swapped Input and Output.")

    def clear_content(self) -> None:
        self.query_one("#urldecode-input", TextArea).text = ""
        self.query_one("#urldecode-output", TextArea).text = ""
        self.notify("Cleared.")
