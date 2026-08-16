import json
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Button, Label, TextArea, Input

from shared.magnet_lab import MagnetLabManager


class MagnetLabTab(Vertical):
    """A tab for Magnet Lab utilities."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.manager = MagnetLabManager()

    def compose(self) -> ComposeResult:
        yield Label("Magnet Lab", id="magnet-lab-header", classes="text-bold")

        with Horizontal(id="magnet-controls", classes="mb-1"):
            yield Button("Parse URI", id="btn-parse", variant="primary")
            yield Button("Build URI", id="btn-build", variant="success")
            yield Button("From Torrent", id="btn-from-torrent", variant="primary")
            yield Button("Clear", id="btn-clear", variant="warning")

        with Horizontal(classes="flex-1"):
            with Vertical(classes="flex-1"):
                yield Label("Input (URI, JSON for Build, or Torrent Path)")
                yield TextArea(id="magnet-input", classes="flex-1")
            with Vertical(classes="flex-1"):
                yield Label("Output")
                yield TextArea(id="magnet-output", classes="flex-1", read_only=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        input_area = self.query_one("#magnet-input", TextArea)
        output_area = self.query_one("#magnet-output", TextArea)
        input_data = input_area.text.strip()

        from rich.markup import escape

        if button_id == "btn-parse":
            if not input_data:
                output_area.text = "Error: Please enter a Magnet URI to parse."
                return

            try:
                parsed = self.manager.parse(input_data)
                output_area.text = json.dumps(parsed, indent=2)
            except Exception as e:
                output_area.text = f"❌ Error parsing Magnet URI:\n{escape(str(e))}"

        elif button_id == "btn-build":
            if not input_data:
                output_area.text = "Error: Please enter JSON components to build URI."
                return

            try:
                components = json.loads(input_data)
                if not isinstance(components, dict):
                    raise ValueError("Input must be a JSON dictionary of components (e.g. {'xt': '...', 'dn': '...'})")
                uri = self.manager.build(components)
                output_area.text = uri
            except json.JSONDecodeError as e:
                output_area.text = f"❌ Input must be valid JSON:\n{escape(str(e))}"
            except Exception as e:
                output_area.text = f"❌ Error building Magnet URI:\n{escape(str(e))}"

        elif button_id == "btn-from-torrent":
            if not input_data:
                output_area.text = "Error: Please enter the path to a .torrent file."
                return

            try:
                with open(input_data, 'rb') as f:
                    torrent_data = f.read()
                uri = self.manager.from_torrent(torrent_data)
                output_area.text = uri
            except FileNotFoundError:
                output_area.text = f"❌ Error: Torrent file not found: {escape(input_data)}"
            except Exception as e:
                output_area.text = f"❌ Error generating Magnet URI from torrent:\n{escape(str(e))}"

        elif button_id == "btn-clear":
            input_area.text = ""
            output_area.text = ""
