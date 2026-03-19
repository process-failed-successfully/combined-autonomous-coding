import codecs
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Button, TextArea
from textual.widget import Widget

class Rot13LabTab(Widget):
    """TUI Tab for ROT13 encoding/decoding."""

    def compose(self) -> ComposeResult:
        with Container(classes="lab-container"):
            # Editor layout
            with Container(classes="editor-pane"):
                yield TextArea(id="rot13-input")
                yield TextArea(id="rot13-output", read_only=False)

            # Controls
            with Container(classes="control-pane"):
                with Horizontal():
                    yield Button("Encode / Decode", id="btn-rot13-toggle", variant="primary")
                    yield Button("Swap Input/Output", id="btn-rot13-swap", variant="warning")
                    yield Button("Clear", id="btn-rot13-clear", variant="error")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if not btn_id:
            return

        input_area = self.query_one("#rot13-input", TextArea)
        output_area = self.query_one("#rot13-output", TextArea)

        if btn_id == "btn-rot13-toggle":
            text = input_area.text
            output_area.text = codecs.encode(text, 'rot_13')
            self.app.notify("Applied ROT13.")
        elif btn_id == "btn-rot13-swap":
            temp = input_area.text
            input_area.text = output_area.text
            output_area.text = temp
            self.app.notify("Swapped.")
        elif btn_id == "btn-rot13-clear":
            input_area.text = ""
            output_area.text = ""
            self.app.notify("Cleared.")
