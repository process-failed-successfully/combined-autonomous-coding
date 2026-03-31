import json
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, TextArea, Label, Static
from textual import on
from shared.json_schema_lab import JsonSchemaManager


class JsonSchemaTab(Container):
    """A Textual tab for generating JSON Schema from JSON."""

    def compose(self) -> ComposeResult:
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
