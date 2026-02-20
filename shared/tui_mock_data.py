from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, DataTable, Button, Input, Select, RichLog
from textual import on
from shared.mock_data import MockDataGenerator


class MockDataTab(Container):
    """Tab for generating mock data interactively."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.schema = {}
        self.generated_data = []

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: Schema Builder
            with Vertical(id="mock-schema-container", classes="stat-box"):
                yield Label("[bold]Schema Builder[/bold]")

                # Add Field Inputs
                with Vertical(classes="stat-box"):
                    yield Input(placeholder="Field Name...", id="mock-field-name")
                    yield Select.from_values(
                        ["string", "int", "float", "boolean", "uuid", "date", "datetime", "email", "name", "choice"],
                        id="mock-field-type",
                        value="string",
                        prompt="Type"
                    )

                    # Options
                    with Horizontal():
                        yield Input(placeholder="Min", id="mock-opt-min", type="number")
                        yield Input(placeholder="Max", id="mock-opt-max", type="number")

                    yield Input(placeholder="Length (string)", id="mock-opt-length", type="integer")
                    yield Input(placeholder="Choices (comma-sep)", id="mock-opt-choices")

                    yield Button("Add Field", id="btn-mock-add-field", variant="primary")

                # Schema Table
                yield Label("[bold]Current Schema[/bold]")
                yield DataTable(id="mock-schema-table")
                yield Button("Remove Selected", id="btn-mock-remove-field", variant="error", disabled=True)

            # Right Pane: Generate & Export
            with Vertical(id="mock-preview-container"):
                yield Label("[bold]Generation[/bold]")

                with Horizontal(classes="stat-box"):
                    yield Input(placeholder="Count (10)", id="mock-count", type="integer", value="10")
                    yield Button("Generate", id="btn-mock-generate", variant="success")

                yield Label("[bold]Preview[/bold]")
                yield DataTable(id="mock-preview-table")

                yield Label("[bold]Export[/bold]")
                with Vertical(classes="stat-box"):
                    with Horizontal():
                        yield Select.from_values(["json", "csv", "sql"], id="mock-export-format", value="json")
                        yield Input(placeholder="Table Name (SQL)", id="mock-table-name", value="mock_data")

                    with Horizontal():
                        yield Input(placeholder="Filename...", id="mock-filename")
                        yield Button("Export / Save", id="btn-mock-export", variant="primary")

                yield RichLog(id="mock-log", markup=True, wrap=True)

    def on_mount(self) -> None:
        # Schema Table
        schema_table = self.query_one("#mock-schema-table", DataTable)
        schema_table.cursor_type = "row"
        schema_table.add_columns("Field", "Type", "Options")

        # Preview Table
        preview_table = self.query_one("#mock-preview-table", DataTable)
        preview_table.cursor_type = "row"

    @on(Button.Pressed, "#btn-mock-add-field")
    def add_field(self) -> None:
        name = self.query_one("#mock-field-name", Input).value
        if not name:
            self.notify("Field name required.", severity="error")
            return

        if name in self.schema:
            self.notify(f"Field '{name}' already exists.", severity="warning")
            return

        field_type = self.query_one("#mock-field-type", Select).value or "string"

        # Collect options
        options = {}

        # Min/Max
        min_val = self.query_one("#mock-opt-min", Input).value
        max_val = self.query_one("#mock-opt-max", Input).value

        if min_val:
            try:
                options["min"] = float(min_val) if "." in min_val else int(min_val)
            except ValueError:
                pass

        if max_val:
            try:
                options["max"] = float(max_val) if "." in max_val else int(max_val)
            except ValueError:
                pass

        # Length
        length_val = self.query_one("#mock-opt-length", Input).value
        if length_val:
            try:
                options["length"] = int(length_val)
            except ValueError:
                pass

        # Choices
        choices_val = self.query_one("#mock-opt-choices", Input).value
        if choices_val:
            options["choices"] = [c.strip() for c in choices_val.split(",") if c.strip()]

        # Store in schema
        # If options is empty, just store type string, else dict
        if options:
            options["type"] = field_type
            self.schema[name] = options
        else:
            self.schema[name] = field_type

        # Update Table
        table = self.query_one("#mock-schema-table", DataTable)
        opts_str = ", ".join([f"{k}={v}" for k, v in options.items() if k != "type"])
        table.add_row(name, field_type, opts_str, key=name)

        # Clear Inputs (except type)
        self.query_one("#mock-field-name", Input).value = ""
        self.query_one("#mock-opt-min", Input).value = ""
        self.query_one("#mock-opt-max", Input).value = ""
        self.query_one("#mock-opt-length", Input).value = ""
        self.query_one("#mock-opt-choices", Input).value = ""

        self.notify(f"Field '{name}' added.")

    @on(DataTable.RowSelected, "#mock-schema-table")
    def on_schema_selected(self, event: DataTable.RowSelected) -> None:
        self.query_one("#btn-mock-remove-field").disabled = False

    @on(Button.Pressed, "#btn-mock-remove-field")
    def remove_field(self) -> None:
        table = self.query_one("#mock-schema-table", DataTable)
        if table.cursor_row is None:
            return

        row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
        name = row_key.value

        if name in self.schema:
            del self.schema[name]
            table.remove_row(row_key)
            self.notify(f"Field '{name}' removed.")
            self.query_one("#btn-mock-remove-field").disabled = True

    @on(Button.Pressed, "#btn-mock-generate")
    def generate_data(self) -> None:
        if not self.schema:
            self.notify("Schema is empty. Add fields first.", severity="warning")
            return

        count_val = self.query_one("#mock-count", Input).value
        try:
            count = int(count_val) if count_val else 10
        except ValueError:
            count = 10

        generator = MockDataGenerator(self.schema)
        self.generated_data = generator.generate(count)

        # Update Preview
        table = self.query_one("#mock-preview-table", DataTable)
        table.clear(columns=True)

        if self.generated_data:
            cols = list(self.generated_data[0].keys())
            table.add_columns(*cols)

            for row in self.generated_data:
                # Convert to string for display
                values = [str(row.get(c, "")) for c in cols]
                table.add_row(*values)

        self.notify(f"Generated {count} rows.")

    @on(Button.Pressed, "#btn-mock-export")
    def export_data(self) -> None:
        if not self.generated_data:
            self.notify("No data to export. Generate first.", severity="warning")
            return

        filename = self.query_one("#mock-filename", Input).value
        if not filename:
            self.notify("Filename required.", severity="error")
            return

        fmt = self.query_one("#mock-export-format", Select).value or "json"
        table_name = self.query_one("#mock-table-name", Input).value or "mock_data"

        # Add extension if missing
        if not filename.endswith(f".{fmt}"):
            filename += f".{fmt}"

        output_path = self.project_dir / filename

        generator = MockDataGenerator(self.schema)
        try:
            content = generator.export(self.generated_data, format=fmt, table_name=table_name)
            output_path.write_text(content, encoding="utf-8")

            log = self.query_one("#mock-log", RichLog)
            log.write(f"Saved to [bold]{output_path}[/bold]")
            self.notify(f"Exported to {filename}")
        except Exception as e:
            self.notify(f"Export failed: {e}", severity="error")
            self.query_one("#mock-log", RichLog).write(f"[red]Error: {e}[/red]")
