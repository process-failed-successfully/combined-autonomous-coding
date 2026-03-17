from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, Button, TextArea, Select, RadioSet, RadioButton

from shared.bson_lab import BsonManager, HAS_BSON


class BsonLabTab(Container):
    """Tab for BSON encoding and decoding."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = BsonManager()

    def compose(self) -> ComposeResult:
        if not HAS_BSON:
            yield Label("[bold red]Error:[/bold red] The 'bson' library is not installed.\n\nPlease install it using: [bold]pip install bson[/bold]")
            return

        yield Label("BSON Lab", id="bson-header", classes="text-bold")

        with Horizontal(id="bson-controls", classes="mb-1"):
            yield RadioSet(
                RadioButton("Encode (JSON -> BSON)", id="bson-encode", value=True),
                RadioButton("Decode (BSON -> JSON)", id="bson-decode"),
                id="bson-mode-radios"
            )

        with Horizontal(id="bson-format-controls", classes="mb-1"):
            yield Label("Input Format (Decode): ")
            yield Select(
                [("Hex", "hex"), ("Raw String", "raw")],
                id="bson-in-format",
                value="hex",
                allow_blank=False
            )
            yield Label(" Output Format (Encode): ")
            yield Select(
                [("Hex", "hex"), ("Raw String", "raw")],
                id="bson-out-format",
                value="hex",
                allow_blank=False
            )

        with Horizontal(id="bson-io", classes="flex-1"):
            with Vertical(classes="flex-1 mr-1"):
                yield Label("Input Data:")
                yield TextArea(id="bson-input", classes="flex-1 input-textarea")

            with Vertical(classes="flex-1"):
                yield Label("Output Data:")
                yield TextArea(id="bson-output", classes="flex-1 output-textarea", read_only=True)

        with Horizontal(id="bson-actions", classes="mt-1"):
            yield Button("Process", id="btn-bson-process", variant="primary")
            yield Button("Clear", id="btn-bson-clear", variant="warning")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "btn-bson-process":
            self.process_data()
        elif button_id == "btn-bson-clear":
            self.query_one("#bson-input", TextArea).text = ""
            self.query_one("#bson-output", TextArea).text = ""

    def process_data(self) -> None:
        input_text = self.query_one("#bson-input", TextArea).text.strip()
        output_area = self.query_one("#bson-output", TextArea)
        mode_radios = self.query_one("#bson-mode-radios", RadioSet)

        # Determine mode
        # The RadioSet has two children. The first is encode, second is decode
        encode_radio = mode_radios.children[0]
        mode_encode = encode_radio.value

        if not input_text:
            output_area.text = "Please enter data to process."
            return

        if mode_encode:
            # Encode: JSON -> BSON
            out_format = self.query_one("#bson-out-format", Select).value
            try:
                import json
                obj = json.loads(input_text)
                encoded = self.manager.encode(obj)

                if out_format == "hex":
                    output_area.text = encoded.hex()
                else:
                    try:
                        output_area.text = encoded.decode('utf-8')
                    except UnicodeDecodeError:
                        output_area.text = str(encoded)
            except Exception as e:
                output_area.text = f"Encode Error:\n{e}"
        else:
            # Decode: BSON -> JSON
            in_format = self.query_one("#bson-in-format", Select).value
            try:
                if in_format == "hex":
                    # Try to strip 0x if present
                    hex_str = input_text[2:] if input_text.startswith(('0x', '0X')) else input_text
                    data_bytes = bytes.fromhex(hex_str.replace(" ", "").replace("\n", ""))
                else:
                    data_bytes = input_text.encode('utf-8', errors='surrogateescape')

                decoded = self.manager.decode(data_bytes)
                import json

                class BytesEncoder(json.JSONEncoder):
                    def default(self, obj):
                        if isinstance(obj, bytes):
                            try:
                                return obj.decode('utf-8')
                            except UnicodeDecodeError:
                                return repr(obj)
                        return super().default(obj)

                output_area.text = json.dumps(decoded, indent=2, cls=BytesEncoder)
            except Exception as e:
                output_area.text = f"Decode Error:\n{e}"
