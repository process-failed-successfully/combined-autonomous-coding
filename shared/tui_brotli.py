import base64
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, Button, TextArea, Select, Checkbox
from textual import on

from shared.brotli_lab import BrotliLabManager

class BrotliLabTab(Container):
    """Tab for Brotli compression and decompression."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = BrotliLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Brotli Compression Lab[/bold]", classes="welcome-text")

            with Horizontal(classes="stat-box"):
                yield Label("Quality (0-11):")
                # Usually brotli quality is 0-11, where 11 is best but slowest
                quality_options = [(str(i), i) for i in range(12)]
                yield Select(options=quality_options, id="brotli-quality", value=11)

                yield Checkbox("Base64 Output/Input (instead of Hex)", id="brotli-base64", value=True)

            with Horizontal():
                with Vertical(classes="stat-box"):
                    yield Label("Original Text")
                    yield TextArea(id="brotli-input-text")
                    yield Button("Compress ->", id="btn-compress", variant="primary")

                with Vertical(classes="stat-box"):
                    yield Label("Compressed Payload")
                    yield TextArea(id="brotli-compressed-text")
                    yield Button("<- Decompress", id="btn-decompress", variant="warning")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-compress":
            self.action_compress()
        elif event.button.id == "btn-decompress":
            self.action_decompress()

    def action_compress(self) -> None:
        input_text = self.query_one("#brotli-input-text", TextArea).text
        if not input_text:
            self.notify("Input text required.", severity="error")
            return

        quality = self.query_one("#brotli-quality", Select).value
        if quality is None:
            quality = 11

        use_base64 = self.query_one("#brotli-base64", Checkbox).value

        try:
            compressed = self.manager.compress(input_text.encode('utf-8'), quality=quality)

            if use_base64:
                out_str = base64.b64encode(compressed).decode('ascii')
            else:
                out_str = compressed.hex()

            self.query_one("#brotli-compressed-text", TextArea).text = out_str
            self.notify("Compression successful.")
        except Exception as e:
            self.notify(f"Compression error: {e}", severity="error")

    def action_decompress(self) -> None:
        compressed_text = self.query_one("#brotli-compressed-text", TextArea).text.strip()
        if not compressed_text:
            self.notify("Compressed text required.", severity="error")
            return

        use_base64 = self.query_one("#brotli-base64", Checkbox).value

        try:
            if use_base64:
                data = base64.b64decode(compressed_text)
            else:
                data = bytes.fromhex(compressed_text)

            decompressed = self.manager.decompress(data)
            self.query_one("#brotli-input-text", TextArea).text = decompressed.decode('utf-8')
            self.notify("Decompression successful.")
        except Exception as e:
            self.notify(f"Decompression error: {e}", severity="error")
