from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, TextArea, Input
from shared.csv2sql_lab import Csv2SqlManager


class Csv2SqlTab(Container):
    """Tab for CSV to SQL Lab."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = Csv2SqlManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]CSV to SQL Converter[/bold]", classes="welcome-text")

            with Horizontal(classes="stat-box"):
                yield Label("Table Name:", classes="label")
                yield Input(placeholder="my_table", id="c2s-table-input", value="my_table")
                yield Label("Delimiter:", classes="label")
                yield Input(placeholder=",", id="c2s-delim-input", value=",")
                yield Button("Convert", id="btn-convert-c2s", variant="primary")

            with Horizontal():
                with Vertical(classes="stat-box"):
                    yield Label("CSV Input (first row must be headers):")
                    yield TextArea(id="c2s-input")

                with Vertical(classes="stat-box"):
                    yield Label("SQL Output:")
                    yield TextArea(id="c2s-output", read_only=True)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-convert-c2s":
            self.convert()

    def convert(self) -> None:
        csv_text = self.query_one("#c2s-input", TextArea).text
        out = self.query_one("#c2s-output", TextArea)
        table_name = self.query_one("#c2s-table-input", Input).value or "my_table"
        delimiter = self.query_one("#c2s-delim-input", Input).value or ","

        if not csv_text.strip():
            self.notify("Input CSV required.", severity="error")
            return

        try:
            sql = self.manager.convert_to_sql(csv_text, table_name=table_name, delimiter=delimiter)
            out.load_text(sql)
            self.notify("Converted to SQL.")
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")
            out.load_text(f"-- Error: {e}")
