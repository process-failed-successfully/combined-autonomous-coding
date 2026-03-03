from textual.app import ComposeResult
from textual.widgets import TabPane, TextArea, Button, Static, Input
from textual.containers import Vertical, Horizontal
import json
import yaml

from shared.schema_lab import SchemaLabManager


class SchemaLabTab(TabPane):
    """A Textual tab for Schema Lab."""

    def __init__(self, project_dir=None):
        super().__init__("Schema Lab", id="tab-schema")
        self.manager = SchemaLabManager(project_dir)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Schema Lab", classes="header")

            with Horizontal():
                with Vertical():
                    yield Static("Input (JSON/YAML Data or Schema)")
                    self.input_area = TextArea(id="schema_input")
                    yield self.input_area

                with Vertical():
                    yield Static("Output")
                    self.output_area = TextArea(id="schema_output", read_only=True)
                    yield self.output_area

            with Horizontal(id="schema_buttons"):
                yield Button("Infer Schema", id="btn_infer", variant="primary")
                yield Button("Convert to TS", id="btn_to_ts")
                yield Button("Convert to Pydantic", id="btn_to_pydantic")

            with Horizontal(id="schema_options"):
                yield Static("Root Name:")
                self.root_name_input = Input(value="Root", id="input_root_name")
                yield self.root_name_input

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        input_text = self.input_area.text.strip()
        root_name = self.root_name_input.value.strip() or "Root"

        if not input_text:
            self.app.notify("Input cannot be empty.", severity="error")
            return

        try:
            # Try parsing as JSON first, then YAML
            try:
                data = json.loads(input_text)
            except json.JSONDecodeError:
                data = yaml.safe_load(input_text)
                if not isinstance(data, (dict, list)):
                    raise ValueError("Input must be valid JSON or YAML objects/arrays.")

            if button_id == "btn_infer":
                schema = self.manager.infer_schema(data)
                self.output_area.text = json.dumps(schema, indent=2)
                self.app.notify("Schema inferred successfully.")
            elif button_id == "btn_to_ts":
                # Assuming input is already a schema
                ts_code = self.manager.to_typescript(data, root_name)
                self.output_area.text = ts_code
                self.app.notify("Converted to TypeScript.")
            elif button_id == "btn_to_pydantic":
                # Assuming input is already a schema
                py_code = self.manager.to_pydantic(data, root_name)
                self.output_area.text = py_code
                self.app.notify("Converted to Pydantic.")

        except Exception as e:
            self.app.notify(f"Error: {e}", severity="error")
