import json
import yaml
from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, Button, TextArea, TabbedContent, TabPane
from textual import on
from shared.schema_lab import SchemaLabManager

class SchemaLabTab(Container):
    """Tab for inferring JSON Schemas and generating TypeScript/Pydantic models."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = SchemaLabManager(project_dir)

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: Input
            with Vertical(id="schema-input-container", classes="stat-box"):
                yield Label("[bold]Input Data (JSON/YAML)[/bold]")
                yield TextArea(id="schema-input", language="json")
                with Horizontal():
                    yield Button("Process", id="btn-schema-process", variant="primary")
                    yield Button("Clear", id="btn-schema-clear", variant="default")

            # Right Pane: Output Tabs
            with Vertical(id="schema-output-container", classes="stat-box"):
                with TabbedContent():
                    with TabPane("JSON Schema", id="schema-tab-json"):
                        yield TextArea(id="schema-output-json", language="json", read_only=True)
                    with TabPane("TypeScript", id="schema-tab-ts"):
                        yield TextArea(id="schema-output-ts", language="typescript", read_only=True)
                    with TabPane("Pydantic", id="schema-tab-pydantic"):
                        yield TextArea(id="schema-output-pydantic", language="python", read_only=True)

    @on(Button.Pressed, "#btn-schema-process")
    def on_process(self) -> None:
        input_data = self.query_one("#schema-input", TextArea).text.strip()
        if not input_data:
            self.notify("Please enter JSON or YAML data.", severity="warning")
            return

        try:
            # Try to parse as JSON first, then YAML
            try:
                parsed_data = json.loads(input_data)
            except json.JSONDecodeError:
                parsed_data = yaml.safe_load(input_data)

            # Infer Schema
            schema = self.manager.infer_schema(parsed_data)
            schema_json = json.dumps(schema, indent=2)

            # Generate TypeScript
            ts_code = self.manager.to_typescript(schema, root_name="Root")

            # Generate Pydantic
            pydantic_code = self.manager.to_pydantic(schema, root_name="Root")

            # Update outputs
            self.query_one("#schema-output-json", TextArea).text = schema_json
            self.query_one("#schema-output-ts", TextArea).text = ts_code
            self.query_one("#schema-output-pydantic", TextArea).text = pydantic_code

            self.notify("Schema inferred and converted successfully.", severity="information")

        except yaml.YAMLError as e:
            self.notify(f"Invalid JSON/YAML: {e}", severity="error")
            self.query_one("#schema-output-json", TextArea).text = f"Error: Invalid JSON/YAML.\n{e}"
            self.query_one("#schema-output-ts", TextArea).text = ""
            self.query_one("#schema-output-pydantic", TextArea).text = ""
        except Exception as e:
            self.notify(f"Error processing data: {e}", severity="error")
            self.query_one("#schema-output-json", TextArea).text = f"Error: {e}"
            self.query_one("#schema-output-ts", TextArea).text = ""
            self.query_one("#schema-output-pydantic", TextArea).text = ""

    @on(Button.Pressed, "#btn-schema-clear")
    def on_clear(self) -> None:
        self.query_one("#schema-input", TextArea).text = ""
        self.query_one("#schema-output-json", TextArea).text = ""
        self.query_one("#schema-output-ts", TextArea).text = ""
        self.query_one("#schema-output-pydantic", TextArea).text = ""
        self.notify("Cleared inputs and outputs.")
