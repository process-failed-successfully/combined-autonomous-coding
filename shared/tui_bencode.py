import json
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Button, Label, TextArea

from shared.bencode_lab import BencodeManager


class BencodeLabTab(Vertical):
    """A tab for Bencode Lab utilities."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.manager = BencodeManager()

    def compose(self) -> ComposeResult:
        yield Label("Bencode Lab", id="bencode-lab-header", classes="text-bold")

        with Horizontal(id="bencode-controls", classes="mb-1"):
            yield Button("Decode Bencode", id="btn-decode", variant="primary")
            yield Button("Encode to Bencode", id="btn-encode", variant="success")
            yield Button("Clear", id="btn-clear", variant="warning")

        with Horizontal(classes="flex-1"):
            with Vertical(classes="flex-1"):
                yield Label("Input")
                yield TextArea(id="bencode-input", classes="flex-1")
            with Vertical(classes="flex-1"):
                yield Label("Output")
                yield TextArea(id="bencode-output", classes="flex-1", read_only=True)

    class BytesEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, bytes):
                try:
                    return obj.decode('utf-8')
                except UnicodeDecodeError:
                    return repr(obj)
            return super().default(obj)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        input_area = self.query_one("#bencode-input", TextArea)
        output_area = self.query_one("#bencode-output", TextArea)
        input_data = input_area.text.strip()

        if button_id == "btn-decode":
            if not input_data:
                output_area.text = "Error: Please enter Bencode string to decode."
                return

            try:
                # Handle hex if prefixed
                if input_data.startswith("0x") or input_data.startswith("0X"):
                    data_bytes = bytes.fromhex(input_data[2:])
                else:
                    data_bytes = input_data.encode('utf-8', errors='surrogateescape')

                decoded = self.manager.decode(data_bytes)
                output_area.text = json.dumps(decoded, indent=2, cls=self.BytesEncoder)
            except Exception as e:
                output_area.text = f"❌ Error decoding Bencode:\n{e}"

        elif button_id == "btn-encode":
            if not input_data:
                output_area.text = "Error: Please enter JSON string to encode."
                return

            try:
                obj = json.loads(input_data)
                encoded = self.manager.encode(obj)
                # Display output as utf-8 or hex
                try:
                    output_area.text = encoded.decode('utf-8')
                except UnicodeDecodeError:
                    output_area.text = f"0x{encoded.hex()}"
            except json.JSONDecodeError as e:
                output_area.text = f"❌ Input must be valid JSON:\n{e}"
            except Exception as e:
                output_area.text = f"❌ Error encoding to Bencode:\n{e}"

        elif button_id == "btn-clear":
            input_area.text = ""
            output_area.text = ""
