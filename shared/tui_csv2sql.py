from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Label, Input, Button, TextArea
from textual.widget import Widget
from textual import on

from shared.csv2sql_lab import Csv2SqlManager


class Csv2SqlTab(Widget):
    """TUI Tab for converting CSV to SQL."""

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("Table Name:")
            yield Input(value="data_table", id="csv2sql-table-input", placeholder="Enter target table name")

            with Horizontal():
                with Vertical(classes="stat-box"):
                    yield Label("Input CSV:")
                    yield TextArea(id="csv2sql-input")

                with Vertical(classes="stat-box"):
                    yield Label("Output SQL:")
                    yield TextArea(id="csv2sql-output", read_only=True)

            with Horizontal():
                yield Button("Convert", id="btn-csv2sql-convert", variant="primary")
                yield Button("Clear", id="btn-csv2sql-clear", variant="error")

    @on(Button.Pressed, "#btn-csv2sql-convert")
    def convert_csv(self) -> None:
        table_input = self.query_one("#csv2sql-table-input", Input)
        csv_input = self.query_one("#csv2sql-input", TextArea)
        sql_output = self.query_one("#csv2sql-output", TextArea)

        csv_text = csv_input.text
        table_name = table_input.value or "data_table"

        manager = Csv2SqlManager()
        try:
            sql_text = manager.convert(csv_text, table_name)
            sql_output.text = sql_text
            self.app.notify("Conversion successful!", title="Success")
        except Exception as e:
            sql_output.text = f"Error: {e}"
            self.app.notify(f"Conversion failed: {e}", title="Error", severity="error")

    @on(Button.Pressed, "#btn-csv2sql-clear")
    def clear_inputs(self) -> None:
        self.query_one("#csv2sql-input", TextArea).text = ""
        self.query_one("#csv2sql-output", TextArea).text = ""
        self.app.notify("Fields cleared")
