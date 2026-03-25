from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Select, TextArea, Static
from textual import on


class OctalTab(Vertical):
    """Interactive Octal Lab TUI."""

    def compose(self) -> ComposeResult:
        with Horizontal(classes="tool-header"):
            yield Static("Octal Encoder/Decoder Lab", classes="tool-title")

        yield Select(
            [("Encode", "encode"), ("Decode", "decode")],
            value="encode",
            id="select-octal-mode",
        )

        with Horizontal(classes="tool-split-view"):
            with Vertical(classes="tool-input-area"):
                yield Static("Input:", classes="label")
                yield TextArea(id="input-octal-text")

            with Vertical(classes="tool-output-area"):
                yield Static("Output:", classes="label")
                yield TextArea(id="output-octal-text", read_only=True)

    @on(TextArea.Changed, "#input-octal-text")
    def on_input_changed(self, event: TextArea.Changed) -> None:
        self.update_output()

    @on(Select.Changed, "#select-octal-mode")
    def on_mode_changed(self, event: Select.Changed) -> None:
        self.update_output()

    def update_output(self) -> None:
        input_widget = self.query_one("#input-octal-text", TextArea)
        output_widget = self.query_one("#output-octal-text", TextArea)
        mode_select = self.query_one("#select-octal-mode", Select)

        text = input_widget.text
        if not text:
            output_widget.text = ""
            return

        mode = mode_select.value
        if mode == Select.BLANK:
            output_widget.text = ""
            return

        try:
            if mode == "encode":
                encoded = " ".join(f"{b:03o}" for b in text.encode('utf-8'))
                output_widget.text = encoded
            elif mode == "decode":
                octal_parts = text.strip().split()
                try:
                    decoded_bytes = bytes(int(p, 8) for p in octal_parts)
                except ValueError:
                    output_widget.text = "Error: Invalid octal string."
                    return
                try:
                    decoded = decoded_bytes.decode('utf-8')
                    output_widget.text = decoded
                except UnicodeDecodeError:
                    output_widget.text = "Error: Decoded bytes are not valid UTF-8."
        except Exception as e:
            output_widget.text = f"Error: {str(e)}"
