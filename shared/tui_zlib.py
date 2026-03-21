from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, TextArea, Select, Switch
from shared.zlib_lab import ZlibLabManager
import base64


class ZlibTab(Container):
    """Tab for Zlib Compression/Decompression."""

    DEFAULT_CSS = """
    ZlibTab {
        layout: vertical;
        height: 100%;
    }

    .zlib-box {
        height: auto;
        border: solid $accent;
        padding: 1;
        margin: 1;
    }

    .zlib-controls {
        height: auto;
        padding: 1;
        margin: 1;
        align: left middle;
    }

    #zlib-input, #zlib-output {
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Zlib Lab (Compress/Decompress)[/bold]", classes="welcome-text")

            # Input Section
            with Vertical(classes="zlib-box"):
                yield Label("Input Text (or Data to Decompress):")
                yield TextArea(id="zlib-input", show_line_numbers=False)

            # Options
            with Horizontal(classes="zlib-controls"):
                yield Label("Format: ")
                yield Select(
                    [("zlib", "zlib"), ("deflate", "deflate"), ("gzip", "gzip")],
                    value="zlib",
                    id="zlib-format",
                )
                yield Label("   Base64 I/O: ")
                yield Switch(value=False, id="zlib-base64")

            # Controls Section
            with Horizontal(classes="zlib-box"):
                yield Button("Compress", id="btn-zlib-compress", variant="primary")
                yield Button("Decompress", id="btn-zlib-decompress", variant="success")
                yield Button("Swap Input/Output", id="btn-zlib-swap", variant="warning")
                yield Button("Clear", id="btn-zlib-clear", variant="error")

            # Output Section
            with Vertical(classes="zlib-box"):
                yield Label("Output Text:")
                yield TextArea(id="zlib-output", read_only=False, show_line_numbers=False)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-zlib-compress":
            self.process(compress=True)
        elif event.button.id == "btn-zlib-decompress":
            self.process(compress=False)
        elif event.button.id == "btn-zlib-swap":
            self.swap_content()
        elif event.button.id == "btn-zlib-clear":
            self.clear_content()

    def process(self, compress: bool) -> None:
        text = self.query_one("#zlib-input", TextArea).text
        output_area = self.query_one("#zlib-output", TextArea)
        format_val = self.query_one("#zlib-format", Select).value
        use_base64 = self.query_one("#zlib-base64", Switch).value

        if not text:
            self.notify("Input is empty.", severity="warning")
            return

        manager = ZlibLabManager()

        try:
            if compress:
                data = text.encode("utf-8")
                compressed = manager.compress(data, format=format_val)
                if use_base64:
                    result = base64.b64encode(compressed).decode("ascii")
                else:
                    result = compressed.hex()
                output_area.text = result
                self.notify("Compression complete.", severity="information")
            else:
                if use_base64:
                    data = base64.b64decode(text.strip())
                else:
                    data = bytes.fromhex(text.strip())

                decompressed = manager.decompress(data, format=format_val)
                result = decompressed.decode("utf-8")
                output_area.text = result
                self.notify("Decompression complete.", severity="information")

        except Exception as e:
            output_area.text = f"Error: {e}"
            self.notify(f"Exception: {e}", severity="error")

    def swap_content(self) -> None:
        input_area = self.query_one("#zlib-input", TextArea)
        output_area = self.query_one("#zlib-output", TextArea)

        temp = input_area.text
        input_area.text = output_area.text
        output_area.text = temp
        self.notify("Swapped Input and Output.")

    def clear_content(self) -> None:
        self.query_one("#zlib-input", TextArea).text = ""
        self.query_one("#zlib-output", TextArea).text = ""
        self.notify("Cleared.")
