from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Static, Label, TextArea, Input, TabPane
import json
import sys

from shared.json2kotlin_lab import Json2KotlinManager

class Json2KotlinTab(TabPane):
    """A tab for JSON to Kotlin conversion."""

    def __init__(self):
        super().__init__("JSON to Kotlin", id="tab-json2kotlin")
        self.manager = Json2KotlinManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal(id="j2k-header"):
                yield Label("Convert JSON payload to Kotlin Data Classes", id="j2k-title")

            with Horizontal(id="j2k-controls"):
                yield Label("Root Class Name:")
                yield Input(value="RootClass", id="j2k-root-name")
                yield Label("Package Name:")
                yield Input(value="com.example", id="j2k-package-name")

            with Horizontal(id="j2k-panes"):
                with Vertical(classes="j2k-pane"):
                    yield Label("JSON Input:")
                    yield TextArea(language="json", id="j2k-input")
                with Vertical(classes="j2k-pane"):
                    yield Label("Kotlin Output:")
                    yield TextArea(language="kotlin", read_only=True, id="j2k-output")

            with Horizontal(id="j2k-buttons"):
                yield Button("Convert", id="btn-j2k-convert", variant="primary")
                yield Button("Clear", id="btn-j2k-clear", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "btn-j2k-convert":
            self.action_convert()
        elif button_id == "btn-j2k-clear":
            self.action_clear()

    def action_convert(self) -> None:
        try:
            input_area = self.query_one("#j2k-input", TextArea)
            output_area = self.query_one("#j2k-output", TextArea)
            root_name_input = self.query_one("#j2k-root-name", Input)
            package_name_input = self.query_one("#j2k-package-name", Input)

            json_text = input_area.text.strip()
            if not json_text:
                output_area.text = "Please enter JSON data."
                return

            root_name = root_name_input.value.strip() or "RootClass"
            package_name = package_name_input.value.strip()

            result = self.manager.convert(json_text, root_name, package_name)
            output_area.text = result

        except Exception as e:
            output_area = self.query_one("#j2k-output", TextArea)
            output_area.text = f"Error: {e}"

    def action_clear(self) -> None:
        self.query_one("#j2k-input", TextArea).text = ""
        self.query_one("#j2k-output", TextArea).text = ""
