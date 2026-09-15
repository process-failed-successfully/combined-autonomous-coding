import json
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Button, Label, TextArea, TabPane
from rich.markup import escape

from shared.magnet_lab import MagnetLabManager

class MagnetLabTab(TabPane):
    """A tab for Magnet Lab utilities."""

    def __init__(self, **kwargs):
        super().__init__("Magnet Lab", id="tab-magnet", **kwargs)
        self.manager = MagnetLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("Magnet Lab", id="magnet-lab-header", classes="text-bold mb-1")

            with Horizontal(classes="mb-1", id="magnet-controls"):
                yield Button("Parse URI", id="btn-parse", variant="primary")
                yield Button("Build URI from JSON", id="btn-build", variant="success")
                yield Button("From .torrent (Hex)", id="btn-from-torrent", variant="secondary")
                yield Button("Clear", id="btn-clear", variant="warning")

            with Horizontal(classes="flex-1"):
                with Vertical(classes="flex-1"):
                    yield Label("Input (URI, JSON, or Hex-encoded .torrent)")
                    yield TextArea(id="magnet-input", classes="flex-1")
                with Vertical(classes="flex-1"):
                    yield Label("Output")
                    yield TextArea(id="magnet-output", classes="flex-1", read_only=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        input_area = self.query_one("#magnet-input", TextArea)
        output_area = self.query_one("#magnet-output", TextArea)
        input_data = input_area.text.strip()

        if button_id == "btn-parse":
            if not input_data:
                output_area.text = "Error: Please enter a Magnet URI to parse."
                return

            try:
                parsed = self.manager.parse(input_data)
                output_area.text = json.dumps(parsed, indent=2)
            except Exception as e:
                output_area.text = escape(f"❌ Error parsing Magnet URI:\n{e}")

        elif button_id == "btn-build":
            if not input_data:
                output_area.text = "Error: Please enter JSON data to build from."
                return

            try:
                data = json.loads(input_data)
                uri = self.manager.build(data)
                output_area.text = uri
            except json.JSONDecodeError as e:
                output_area.text = escape(f"❌ Input must be valid JSON:\n{e}")
            except Exception as e:
                output_area.text = escape(f"❌ Error building Magnet URI:\n{e}")

        elif button_id == "btn-from-torrent":
            if not input_data:
                output_area.text = "Error: Please enter Hex-encoded .torrent data."
                return

            try:
                # Remove optional 0x prefix
                hex_str = input_data
                if hex_str.startswith("0x") or hex_str.startswith("0X"):
                    hex_str = hex_str[2:]

                # Clean up whitespaces/newlines for robust hex parsing
                hex_str = "".join(hex_str.split())

                torrent_bytes = bytes.fromhex(hex_str)
                uri = self.manager.from_torrent(torrent_bytes)
                output_area.text = uri
            except ValueError as e:
                output_area.text = escape(f"❌ Error parsing hex or torrent data:\n{e}")
            except Exception as e:
                output_area.text = escape(f"❌ Error generating Magnet URI:\n{e}")

        elif button_id == "btn-clear":
            input_area.text = ""
            output_area.text = ""
