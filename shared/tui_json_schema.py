import json
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, TextArea, Label, Static, TabbedContent, TabPane
from textual import on
from shared.json_schema_lab import JsonSchemaManager


class JsonSchemaTab(Container):
    """A Textual tab for generating and validating JSON Schema."""

    def compose(self) -> ComposeResult:
        with TabbedContent():
            with TabPane("Generate Schema", id="tab-json-schema-gen"):
                yield Vertical(
                    Label("Input JSON:"),
                    TextArea(id="json-schema-input", language="json", classes="h-1-3"),

                    Horizontal(
                        Button("Generate Schema", id="btn-generate-json-schema", variant="primary"),
                        Button("Clear", id="btn-clear-json-schema", variant="error"),
                        classes="button-row py-1"
                    ),

                    Label("Output JSON Schema:"),
                    TextArea(id="json-schema-output", language="json", read_only=True, classes="h-1-3"),

                    Static("", id="json-schema-status", classes="mt-1 status-text"),
                    classes="p-2"
                )

            with TabPane("Validate JSON", id="tab-json-schema-val"):
                yield Vertical(
                    Horizontal(
                        Vertical(
                            Label("Input JSON:"),
                            TextArea(id="json-schema-val-data", language="json", classes="h-full")
                        ),
                        Vertical(
                            Label("JSON Schema:"),
                            TextArea(id="json-schema-val-schema", language="json", classes="h-full")
                        ),
                        classes="h-2-3"
                    ),

                    Horizontal(
                        Button("Validate", id="btn-validate-json-schema", variant="primary"),
                        Button("Clear", id="btn-clear-validate-json-schema", variant="error"),
                        classes="button-row py-1"
                    ),

                    Static("", id="json-schema-val-status", classes="mt-1 status-text"),
                    classes="p-2"
                )

    @on(Button.Pressed, "#btn-generate-json-schema")
    def on_generate(self) -> None:
        input_widget = self.query_one("#json-schema-input", TextArea)
        output_widget = self.query_one("#json-schema-output", TextArea)
        status_widget = self.query_one("#json-schema-status", Static)

        text = input_widget.text
        if not text:
            status_widget.update("[red]Please enter JSON to generate a schema.[/red]")
            return

        try:
            data = json.loads(text)
            manager = JsonSchemaManager()
            schema = manager.generate(data)
            output_widget.text = json.dumps(schema, indent=2)
            status_widget.update("[green]Successfully generated JSON Schema.[/green]")
        except json.JSONDecodeError as e:
            status_widget.update(f"[red]Invalid JSON: {e}[/red]")
        except Exception as e:
            status_widget.update(f"[red]Error: {e}[/red]")

    @on(Button.Pressed, "#btn-clear-json-schema")
    def on_clear(self) -> None:
        self.query_one("#json-schema-input", TextArea).text = ""
        self.query_one("#json-schema-output", TextArea).text = ""
        self.query_one("#json-schema-status", Static).update("")

    @on(Button.Pressed, "#btn-validate-json-schema")
    def on_validate(self) -> None:
        data_widget = self.query_one("#json-schema-val-data", TextArea)
        schema_widget = self.query_one("#json-schema-val-schema", TextArea)
        status_widget = self.query_one("#json-schema-val-status", Static)

        data_text = data_widget.text
        schema_text = schema_widget.text

        if not data_text or not schema_text:
            status_widget.update("[red]Please enter both JSON Data and JSON Schema.[/red]")
            return

        try:
            data = json.loads(data_text)
        except json.JSONDecodeError as e:
            status_widget.update(f"[red]Invalid JSON Data: {e}[/red]")
            return

        try:
            schema = json.loads(schema_text)
        except json.JSONDecodeError as e:
            status_widget.update(f"[red]Invalid JSON Schema: {e}[/red]")
            return

        manager = JsonSchemaManager()
        result = manager.validate(data, schema)

        if result.get("success"):
            status_widget.update("[green]✅ JSON is valid according to the schema.[/green]")
        else:
            error_msg = result.get("error", "Unknown error")
            path_msg = f" at /{'/'.join(map(str, result['path']))}" if result.get("path") else ""
            status_widget.update(f"[red]❌ Validation failed: {error_msg}{path_msg}[/red]")

    @on(Button.Pressed, "#btn-clear-validate-json-schema")
    def on_clear_validate(self) -> None:
        self.query_one("#json-schema-val-data", TextArea).text = ""
        self.query_one("#json-schema-val-schema", TextArea).text = ""
        self.query_one("#json-schema-val-status", Static).update("")
