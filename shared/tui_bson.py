from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.widgets import Static, Button, Label, TextArea
from textual.reactive import reactive


class BsonLabTab(Container):
    """A TUI tab for BSON encoding and decoding."""

    input_data = reactive("")
    output_data = reactive("")
    error_message = reactive("")
    mode = reactive("encode")  # encode | decode

    def compose(self) -> ComposeResult:
        yield VerticalScroll(
            Horizontal(
                Button("Encode JSON -> BSON (Hex)", id="btn_encode", variant="primary"),
                Button("Decode BSON (Hex) -> JSON", id="btn_decode"),
                classes="mode-buttons",
                id="controls"
            ),
            Label("Input:", classes="section-label"),
            TextArea(id="input_area"),
            Label("Output:", classes="section-label"),
            TextArea(id="output_area", read_only=True),
            Static(id="error_display", classes="error-text")
        )

    def on_mount(self) -> None:
        try:
            import bson  # noqa: F401
            self.has_bson = True
        except ImportError:
            self.has_bson = False
            self.error_message = "Error: 'bson' module not installed. Please 'pip install pymongo' or 'bson'."

    def watch_error_message(self, old_val: str, new_val: str) -> None:
        err_display = self.query_one("#error_display", Static)
        err_display.update(new_val)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if not self.has_bson:
            self.error_message = "Cannot run without 'bson' installed."
            return

        from shared.bson_lab import BsonManager

        btn_id = event.button.id
        input_text = self.query_one("#input_area", TextArea).text
        self.error_message = ""
        output_area = self.query_one("#output_area", TextArea)

        if btn_id == "btn_encode":
            self.mode = "encode"
            try:
                encoded = BsonManager.encode(input_text)
                output_area.text = encoded.hex()
            except Exception as e:
                self.error_message = f"Encode Error: {e}"
        elif btn_id == "btn_decode":
            self.mode = "decode"
            try:
                data_bytes = bytes.fromhex(input_text.strip())
                decoded = BsonManager.decode(data_bytes)
                output_area.text = decoded
            except Exception as e:
                self.error_message = f"Decode Error: {e}"
