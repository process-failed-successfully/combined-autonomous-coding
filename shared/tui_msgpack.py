from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Label, Button, TextArea
from textual.containers import ScrollableContainer

from shared.msgpack_lab import MsgpackManager


class MsgpackLabTab(ScrollableContainer):
    """TUI Tab for MessagePack Lab."""

    def __init__(self, project_dir=None, **kwargs):
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = MsgpackManager()

    def compose(self) -> ComposeResult:
        with Vertical(classes="tab-content"):
            yield Label("[bold]MessagePack Lab[/bold] - Encode and Decode MessagePack Data", classes="tab-title")

            with Horizontal(classes="action-bar"):
                yield Button("Encode JSON to Msgpack", id="btn-msgpack-encode", variant="primary")
                yield Button("Decode Msgpack to JSON", id="btn-msgpack-decode", variant="success")
                yield Button("Clear", id="btn-msgpack-clear", variant="warning")

            with Horizontal():
                with Vertical(classes="panel"):
                    yield Label("JSON Input / Output:")
                    yield TextArea(id="msgpack-json-area")

                with Vertical(classes="panel"):
                    yield Label("MessagePack Input / Output (Base64):")
                    yield TextArea(id="msgpack-b64-area")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-msgpack-encode":
            self.encode()
        elif event.button.id == "btn-msgpack-decode":
            self.decode()
        elif event.button.id == "btn-msgpack-clear":
            self.clear_all()

    def encode(self) -> None:
        json_area = self.query_one("#msgpack-json-area", TextArea)
        b64_area = self.query_one("#msgpack-b64-area", TextArea)
        text = json_area.text.strip()

        if not text:
            self.app.notify("JSON input required for encoding.", severity="error")
            return

        try:
            res = self.manager.encode(text)
            b64_area.text = res
            self.app.notify("Encoded to MessagePack successfully.")
        except Exception as e:
            self.app.notify(f"Encoding Error: {e}", severity="error")

    def decode(self) -> None:
        json_area = self.query_one("#msgpack-json-area", TextArea)
        b64_area = self.query_one("#msgpack-b64-area", TextArea)
        b64_str = b64_area.text.strip()

        if not b64_str:
            self.app.notify("MessagePack (Base64) input required for decoding.", severity="error")
            return

        try:
            res = self.manager.decode(b64_str)
            json_area.text = res
            self.app.notify("Decoded from MessagePack successfully.")
        except Exception as e:
            self.app.notify(f"Decoding Error: {e}", severity="error")

    def clear_all(self) -> None:
        self.query_one("#msgpack-json-area", TextArea).text = ""
        self.query_one("#msgpack-b64-area", TextArea).text = ""
        self.app.notify("Fields cleared.")
