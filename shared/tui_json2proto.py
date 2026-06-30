from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Header, Footer, Static, TextArea, Input, Label
from textual.binding import Binding

from shared.json2proto_lab import Json2ProtoManager

class Json2ProtoLabTab(Container):
    """Tab for Json2Proto Lab."""

    BINDINGS = [
        Binding("ctrl+r", "convert", "Convert"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.manager = Json2ProtoManager()

    def compose(self) -> ComposeResult:
        yield Label("JSON to Protobuf Converter", classes="welcome-text")

        with Horizontal(classes="stat-box"):
            yield Label("Root Message Name:")
            yield Input(value="RootMessage", id="input-root-name")
            yield Button("Convert (Ctrl+R)", id="btn-convert", variant="primary")

        with Horizontal():
            with Vertical():
                yield Label("JSON Input:")
                yield TextArea(id="input-json", language="json")
            with Vertical():
                yield Label("Protobuf Output:")
                yield TextArea(id="output-proto", read_only=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-convert":
            self.action_convert()

    def action_convert(self) -> None:
        json_input = self.query_one("#input-json", TextArea).text
        root_name = self.query_one("#input-root-name", Input).value or "RootMessage"
        output_area = self.query_one("#output-proto", TextArea)

        if not json_input.strip():
            self.app.notify("Error: JSON input is empty.", severity="error")
            return

        try:
            proto_output = self.manager.convert(json_input, root_name)
            output_area.text = proto_output
            self.app.notify("Converted to Protobuf successfully.")
        except Exception as e:
            output_area.text = f"// Error: {e}"
            self.app.notify(f"Error: {e}", severity="error")
