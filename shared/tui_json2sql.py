from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.widgets import TextArea, Button, Static, Input
from shared.json2sql_lab import Json2SqlManager


class Json2SqlTab(Container):
    """TUI Tab for converting JSON to SQL INSERT statements."""

    def __init__(self, project_dir=None):
        super().__init__()
        self.project_dir = project_dir
        self.manager = Json2SqlManager()

    def compose(self) -> ComposeResult:
        yield Static("[bold]JSON to SQL Lab[/bold] - Convert JSON data to SQL INSERT statements", classes="tab-title")
        with Horizontal():
            with VerticalScroll(classes="stat-box"):
                yield Static("Input JSON:", classes="label")
                self.input_area = TextArea(text='[\n  {"id": 1, "name": "Alice"},\n  {"id": 2, "name": "Bob"}\n]', language="json", id="json2sql-input")
                yield self.input_area
                yield Static("Table Name:", classes="label")
                self.table_input = Input(value="mytable", placeholder="Enter table name...", id="json2sql-table")
                yield self.table_input
                yield Button("Convert", id="btn-convert-json2sql", variant="primary")

            with VerticalScroll(classes="stat-box"):
                yield Static("Output SQL:", classes="label")
                self.output_area = TextArea(language="sql", read_only=True, id="json2sql-output")
                yield self.output_area

    def on_mount(self) -> None:
        self.input_area.focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-convert-json2sql":
            self.convert()

    def convert(self) -> None:
        json_str = self.input_area.text
        table_name = self.table_input.value

        if not json_str.strip():
            self.output_area.text = "-- Error: Input JSON is empty."
            return

        if not table_name.strip():
            self.output_area.text = "-- Error: Table name is required."
            return

        result = self.manager.convert(json_str, table_name)
        if not result["success"]:
            self.output_area.text = f"-- Error: {result.get('error', 'Unknown error')}"
        else:
            self.output_area.text = result["sql"]
