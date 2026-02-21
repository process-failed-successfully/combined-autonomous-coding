from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, Select, TextArea
from shared.codec_lab import CodecLabManager


class CodecLabTab(Container):
    """Tab for Text Encoding/Decoding (Codec)."""

    DEFAULT_CSS = """
    CodecLabTab {
        layout: vertical;
        height: 100%;
    }

    .codec-box {
        height: auto;
        border: solid $accent;
        padding: 1;
        margin: 1;
    }

    #codec-input, #codec-output {
        height: 1fr;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = CodecLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Codec Lab (Encoder/Decoder)[/bold]", classes="welcome-text")

            # Input Section
            with Vertical(classes="codec-box"):
                yield Label("Input Text:")
                yield TextArea(id="codec-input")

            # Controls Section
            with Horizontal(classes="codec-box"):
                yield Label("Algorithm:", classes="label")
                yield Select.from_values(
                    [
                        "Base64",
                        "Hex",
                        "HTML Entities",
                        "URL",
                        "Rot13",
                        "Binary",
                        "Unicode Escape",
                        "Leet Speak"
                    ],
                    id="codec-algo",
                    value="Base64"
                )

                yield Button("Encode", id="btn-codec-encode", variant="primary")
                yield Button("Decode", id="btn-codec-decode", variant="success")
                yield Button("Swap Input/Output", id="btn-codec-swap", variant="warning")
                yield Button("Clear", id="btn-codec-clear", variant="error")

            # Output Section
            with Vertical(classes="codec-box"):
                yield Label("Output Text:")
                yield TextArea(id="codec-output", read_only=False)  # Editable so user can copy easily

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-codec-encode":
            self.process(encode=True)
        elif event.button.id == "btn-codec-decode":
            self.process(encode=False)
        elif event.button.id == "btn-codec-swap":
            self.swap_content()
        elif event.button.id == "btn-codec-clear":
            self.clear_content()

    def process(self, encode: bool) -> None:
        algo = self.query_one("#codec-algo", Select).value
        text = self.query_one("#codec-input", TextArea).text
        output_area = self.query_one("#codec-output", TextArea)

        if not text:
            self.notify("Input is empty.", severity="warning")
            return

        result = ""
        try:
            if algo == "Base64":
                result = self.manager.base64_encode(text) if encode else self.manager.base64_decode(text)
            elif algo == "Hex":
                result = self.manager.hex_encode(text) if encode else self.manager.hex_decode(text)
            elif algo == "HTML Entities":
                result = self.manager.html_encode(text) if encode else self.manager.html_decode(text)
            elif algo == "URL":
                result = self.manager.url_encode(text) if encode else self.manager.url_decode(text)
            elif algo == "Rot13":
                # Rot13 is symmetric
                result = self.manager.rot13(text)
            elif algo == "Binary":
                result = self.manager.binary_encode(text) if encode else self.manager.binary_decode(text)
            elif algo == "Unicode Escape":
                result = self.manager.unicode_escape(text) if encode else self.manager.unicode_unescape(text)
            elif algo == "Leet Speak":
                if encode:
                    result = self.manager.leet_speak(text)
                else:
                    result = "Leet speak decoding is ambiguous and not supported."

            output_area.text = result

            # Check for error messages in result (simple check based on return values from manager)
            if result.startswith("Error:"):
                self.notify("Operation failed.", severity="error")
            else:
                self.notify("Done.")

        except Exception as e:
            output_area.text = f"Error: {e}"
            self.notify(f"Exception: {e}", severity="error")

    def swap_content(self) -> None:
        input_area = self.query_one("#codec-input", TextArea)
        output_area = self.query_one("#codec-output", TextArea)

        temp = input_area.text
        input_area.text = output_area.text
        output_area.text = temp
        self.notify("Swapped Input and Output.")

    def clear_content(self) -> None:
        self.query_one("#codec-input", TextArea).text = ""
        self.query_one("#codec-output", TextArea).text = ""
        self.notify("Cleared.")
