import json
import yaml
from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Label, Button, TextArea, Select, TabbedContent, TabPane
from textual.containers import Container, Horizontal, Vertical
from textual import on
from shared.schema_lab import SchemaLabManager


class SchemaLabTab(Container):
    """
    Tab for schema inference and conversion.
    """
    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = SchemaLabManager(project_dir)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Schema Lab[/bold]", classes="welcome-text")

            with TabbedContent(id="tabs"):
                # Tab 1: Infer Schema
                with TabPane("Infer Schema", id="tab-infer"):
                    with Horizontal(classes="stat-box"):
                        yield Select.from_values(["JSON", "YAML"], id="infer-fmt", value="JSON", allow_blank=False)
                        yield Button("Infer Schema", id="btn-infer", variant="primary")
                        yield Button("Clear", id="btn-infer-clear", variant="error")

                    with Horizontal():
                        with Vertical(classes="stat-box"):
                            yield Label("Input Data:")
                            yield TextArea(id="infer-input", language="json")

                        with Vertical(classes="stat-box"):
                            yield Label("Inferred Schema:")
                            yield TextArea(id="infer-output", read_only=True, language="json")

                # Tab 2: Convert Schema
                with TabPane("Convert Schema", id="tab-convert"):
                    with Horizontal(classes="stat-box"):
                        yield Select.from_values(["TypeScript Interface", "Pydantic Model"], id="convert-target", value="TypeScript Interface", allow_blank=False)
                        yield Button("Convert", id="btn-convert", variant="primary")
                        yield Button("Clear", id="btn-convert-clear", variant="error")

                    with Horizontal():
                        with Vertical(classes="stat-box"):
                            yield Label("JSON Schema:")
                            yield TextArea(id="convert-input", language="json")

                        with Vertical(classes="stat-box"):
                            yield Label("Generated Types/Models:")
                            yield TextArea(id="convert-output", read_only=True, language="typescript")

    @on(Button.Pressed, "#btn-infer")
    def on_infer(self) -> None:
        inp = self.query_one("#infer-input", TextArea).text
        fmt = self.query_one("#infer-fmt", Select).value
        output_area = self.query_one("#infer-output", TextArea)

        if not inp.strip():
            self.notify("Input required.", severity="error")
            return

        fmt_str = str(fmt) if fmt is not None else "JSON"

        try:
            if fmt_str == "JSON":
                data = json.loads(inp)
            else:
                data = yaml.safe_load(inp)

            schema = self.manager.infer_schema(data)
            output_area.text = json.dumps(schema, indent=2)
            self.notify("Schema inferred successfully.")
        except Exception as e:
            output_area.text = f"# Error: {e}"
            self.notify("Inference failed.", severity="error")

    @on(Button.Pressed, "#btn-infer-clear")
    def on_infer_clear(self) -> None:
        self.query_one("#infer-input", TextArea).text = ""
        self.query_one("#infer-output", TextArea).text = ""

    @on(Button.Pressed, "#btn-convert")
    def on_convert(self) -> None:
        inp = self.query_one("#convert-input", TextArea).text
        target = self.query_one("#convert-target", Select).value
        output_area = self.query_one("#convert-output", TextArea)

        if not inp.strip():
            self.notify("Input required.", severity="error")
            return

        target_str = str(target) if target is not None else ""

        try:
            schema = json.loads(inp)

            if "TypeScript" in target_str:
                output_area.language = "typescript"
                result = self.manager.to_typescript(schema, "RootInterface")
            else:
                output_area.language = "python"
                result = self.manager.to_pydantic(schema, "RootModel")

            output_area.text = result
            self.notify("Conversion complete.")
        except Exception as e:
            output_area.text = f"# Error: {e}"
            self.notify("Conversion failed.", severity="error")

    @on(Button.Pressed, "#btn-convert-clear")
    def on_convert_clear(self) -> None:
        self.query_one("#convert-input", TextArea).text = ""
        self.query_one("#convert-output", TextArea).text = ""
