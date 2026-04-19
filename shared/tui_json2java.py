from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Static, Label, TextArea, Input, TabPane
import json
import sys

from shared.json2java_lab import Json2JavaManager

class Json2JavaTab(TabPane):
    """A tab for JSON to Java conversion."""

    def __init__(self):
        super().__init__("JSON to Java", id="tab-json2java")
        self.manager = Json2JavaManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal(id="j2j-header"):
                yield Label("Convert JSON payload to Java Classes", id="j2j-title")

            with Horizontal(id="j2j-controls"):
                yield Label("Root Class Name:")
                yield Input(value="RootObject", id="j2j-root-name")
                yield Label("Package Name:")
                yield Input(value="com.example", id="j2j-package-name")

            with Horizontal(id="j2j-panes"):
                with Vertical(classes="j2j-pane"):
                    yield Label("JSON Input:")
                    yield TextArea(language="json", id="j2j-input")
                with Vertical(classes="j2j-pane"):
                    yield Label("Java Output:")
                    yield TextArea(language="java", read_only=True, id="j2j-output")

            with Horizontal(id="j2j-buttons"):
                yield Button("Convert", id="btn-j2j-convert", variant="primary")
                yield Button("Clear", id="btn-j2j-clear", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "btn-j2j-convert":
            self.action_convert()
        elif button_id == "btn-j2j-clear":
            self.action_clear()

    def action_convert(self) -> None:
        try:
            input_area = self.query_one("#j2j-input", TextArea)
            output_area = self.query_one("#j2j-output", TextArea)
            root_name_input = self.query_one("#j2j-root-name", Input)
            package_name_input = self.query_one("#j2j-package-name", Input)

            json_text = input_area.text.strip()
            if not json_text:
                output_area.text = "Please enter JSON data."
                return

            root_name = root_name_input.value.strip() or "RootObject"
            package_name = package_name_input.value.strip()

            result = self.manager.convert(json_text, root_name, package_name)
            output_area.text = result

        except Exception as e:
            output_area = self.query_one("#j2j-output", TextArea)
            output_area.text = f"Error: {e}"

    def action_clear(self) -> None:
        self.query_one("#j2j-input", TextArea).text = ""
        self.query_one("#j2j-output", TextArea).text = ""
