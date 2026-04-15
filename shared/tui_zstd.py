from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Label, TextArea, Checkbox, Select
from textual import on

from shared.zstd_lab import ZstdLabManager
import base64


class ZstdLabTab(Container):
    """Tab for Zstandard compression and decompression."""

    def __init__(self):
        super().__init__()
        self.manager = ZstdLabManager()

    def compose(self) -> ComposeResult:
        with Vertical(id="zstd-container"):
            yield Label("[bold]Zstandard Compression Lab[/bold]", classes="welcome-text")

            with Vertical(classes="zstd-controls"):
                # Zstandard compression levels are usually 1 to 22. Default is 3.
                level_options = [(str(i), i) for i in range(1, 23)]
                yield Select(options=level_options, id="zstd-level", value=3)
                yield Checkbox("Base64 Output/Input (instead of Hex)", id="zstd-base64", value=True)

            with Vertical(classes="zstd-panels"):
                with Vertical(classes="zstd-panel"):
                    yield Label("Uncompressed Text:")
                    yield TextArea(id="zstd-input-text")

                with Vertical(classes="zstd-panel"):
                    yield Label("Compressed Payload (Hex or Base64):")
                    yield TextArea(id="zstd-compressed-text")

    @on(TextArea.Changed, "#zstd-input-text")
    def on_input_text_changed(self, event: TextArea.Changed) -> None:
        """When the user types uncompressed text, compress it."""
        if not event.text_area.has_focus:
            return
        input_text = self.query_one("#zstd-input-text", TextArea).text
        if not input_text:
            self.query_one("#zstd-compressed-text", TextArea).text = ""
            return

        level = self.query_one("#zstd-level", Select).value
        # If the level select isn't ready yet or holds an invalid value, fallback
        if level is None or level is Select.BLANK:
            level = 3

        use_base64 = self.query_one("#zstd-base64", Checkbox).value

        try:
            compressed = self.manager.compress(input_text.encode('utf-8'), level=level)
            if use_base64:
                out_str = base64.b64encode(compressed).decode('ascii')
            else:
                out_str = compressed.hex()
            self.query_one("#zstd-compressed-text", TextArea).text = out_str
        except Exception as e:
            self.query_one("#zstd-compressed-text", TextArea).text = f"Error: {e}"

    @on(TextArea.Changed, "#zstd-compressed-text")
    def on_compressed_text_changed(self, event: TextArea.Changed) -> None:
        """When the user modifies the compressed data, try to decompress it."""
        if not event.text_area.has_focus:
            return
        compressed_text = self.query_one("#zstd-compressed-text", TextArea).text.strip()
        if not compressed_text:
            self.query_one("#zstd-input-text", TextArea).text = ""
            return

        use_base64 = self.query_one("#zstd-base64", Checkbox).value

        try:
            if use_base64:
                data = base64.b64decode(compressed_text)
            else:
                data = bytes.fromhex(compressed_text)

            decompressed = self.manager.decompress(data)
            self.query_one("#zstd-input-text", TextArea).text = decompressed.decode('utf-8')
        except Exception as e:
            # Optionally show an error somewhere, but typical in these TUI tools is to just not update
            # the other pane if it's currently invalid hex/base64 or not fully pasted.
            pass

    @on(Select.Changed, "#zstd-level")
    @on(Checkbox.Changed, "#zstd-base64")
    def on_settings_changed(self) -> None:
        """When settings change, trigger re-compression if there's input text."""
        # Just simulate a change on the input text to re-trigger compression
        input_area = self.query_one("#zstd-input-text", TextArea)
        if input_area.text:
            # Only trigger if it has text, to avoid clearing error states needlessly
            # We artificially focus it for the event check
            was_focused = input_area.has_focus
            input_area.focus()
            self.on_input_text_changed(TextArea.Changed(input_area))
            if not was_focused:
                self.query_one("#zstd-base64", Checkbox).focus()
