from textual.app import ComposeResult
from textual.widgets import TextArea, Button, Static, Label, Select
from textual.containers import Vertical, Horizontal, Container
import json

from shared.env2json_lab import Env2JsonManager


class Env2JsonTab(Container):
    """A Textual tab for converting .env to JSON and vice-versa."""

    def __init__(self, project_dir=None):
        super().__init__(id="tab-env2json")
        self.manager = Env2JsonManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(".env / JSON Converter", classes="header")

            with Horizontal(classes="h-auto p-1 border-b border-primary"):
                yield Label("Mode:", classes="p-1 mt-1")
                yield Select(
                    [("Env to JSON", "env2json"), ("JSON to Env", "json2env")],
                    value="env2json",
                    id="env2json_mode_select",
                    classes="w-1-3 m-1"
                )
                yield Button("Convert", id="btn_convert", variant="primary", classes="m-1")
                yield Button("Clear", id="btn_clear", variant="error", classes="m-1")

            with Horizontal(classes="h-full"):
                with Vertical(classes="w-1-2 p-1 border-r border-primary h-full"):
                    yield Label("Input:", classes="text-bold mb-1")
                    self.input_area = TextArea(id="env2json_input", classes="h-full")
                    yield self.input_area

                with Vertical(classes="w-1-2 p-1 h-full"):
                    yield Label("Output:", classes="text-bold mb-1")
                    self.output_area = TextArea(id="env2json_output", read_only=True, classes="h-full")
                    yield self.output_area

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id

        if button_id == "btn_clear":
            self.input_area.text = ""
            self.output_area.text = ""
            return

        input_text = self.input_area.text.strip()
        if not input_text:
            self.app.notify("Input cannot be empty.", severity="error")
            return

        if button_id == "btn_convert":
            mode_select = self.query_one("#env2json_mode_select", Select)
            mode = mode_select.value

            if mode == Select.BLANK or not isinstance(mode, str):
                self.app.notify("Please select a conversion mode.", severity="error")
                return

            try:
                if mode == "env2json":
                    json_data = self.manager.env_to_json(input_text)
                    self.output_area.text = json.dumps(json_data, indent=2)
                    self.output_area.language = "json"
                elif mode == "json2env":
                    env_data = self.manager.json_to_env(input_text)
                    self.output_area.text = env_data
                    self.output_area.language = "text"

                self.app.notify("Converted successfully.")
            except Exception as e:
                self.app.notify(f"Conversion Error: {e}", severity="error")
