from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Input, TextArea, DataTable, Label, Switch
from shared.sqlite_lab import SqliteLabManager
from pathlib import Path


class SqliteLabTab(Container):
    """Tab for SQLite Lab to interactively query databases."""

    DEFAULT_CSS = """
    SqliteLabTab {
        layout: vertical;
        height: 100%;
    }

    .row {
        height: auto;
        margin: 1;
        align: left middle;
    }

    #sqlite-db-path {
        width: 40;
    }

    .query-box {
        height: 10;
        margin: 1;
        border: solid $accent;
    }

    .query-actions {
        height: auto;
        margin-left: 1;
        margin-bottom: 1;
    }

    #sqlite-table {
        height: 1fr;
        margin: 1;
        border: solid $secondary;
    }

    .status-msg {
        color: $warning;
        margin-left: 2;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = SqliteLabManager()
        self.current_db = ":memory:"

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]SQLite Lab[/bold]", classes="welcome-text")

            with Horizontal(classes="row"):
                yield Label("Database Path:", classes="lbl")
                yield Input(id="sqlite-db-path", placeholder=":memory: or path/to/db.sqlite", value=":memory:")
                yield Button("Connect", id="btn-sqlite-connect", variant="primary")
                yield Button("List Tables", id="btn-sqlite-tables", variant="default")
                yield Button("Show Schema", id="btn-sqlite-schema", variant="default")
                yield Label("", id="sqlite-status", classes="status-msg")

            with Vertical(classes="query-box"):
                yield TextArea(id="sqlite-query", text="SELECT sqlite_version();")

            with Horizontal(classes="query-actions"):
                yield Button("Execute Query", id="btn-sqlite-exec", variant="success")
                yield Button("Clear Query", id="btn-sqlite-clear", variant="error")
                yield Button("Export CSV", id="btn-sqlite-csv", variant="primary")

            yield DataTable(id="sqlite-table")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if not btn_id:
            return

        status_lbl = self.query_one("#sqlite-status", Label)

        if btn_id == "btn-sqlite-connect":
            db_path = self.query_one("#sqlite-db-path", Input).value.strip() or ":memory:"
            try:
                # Close old connection if any
                self.manager.close()
                self.manager = SqliteLabManager(db_path)
                self.manager.connect()
                self.current_db = db_path
                status_lbl.update(f"Connected to {db_path}")
                self.notify(f"Connected to {db_path}")
            except Exception as e:
                status_lbl.update(f"Error: {e}")
                self.notify(f"Connection error: {e}", severity="error")

        elif btn_id == "btn-sqlite-tables":
            try:
                tables = self.manager.get_tables()
                if not tables:
                    self.display_message("No tables found in database.")
                else:
                    self.display_data(["Table Name"], [{"Table Name": t} for t in tables])
            except Exception as e:
                self.notify(f"Error: {e}", severity="error")

        elif btn_id == "btn-sqlite-schema":
            try:
                schema = self.manager.get_schema()
                self.display_message(schema)
            except Exception as e:
                self.notify(f"Error: {e}", severity="error")

        elif btn_id == "btn-sqlite-exec":
            query = self.query_one("#sqlite-query", TextArea).text.strip()
            if not query:
                self.notify("Query is empty.", severity="warning")
                return
            try:
                columns, rows = self.manager.execute_query(query)
                if not columns and not rows:
                    self.display_message("Query executed successfully. No data returned.")
                else:
                    self.display_data(columns, rows)
            except Exception as e:
                self.notify(f"Query Error: {e}", severity="error")

        elif btn_id == "btn-sqlite-clear":
            self.query_one("#sqlite-query", TextArea).text = ""

        elif btn_id == "btn-sqlite-csv":
            query = self.query_one("#sqlite-query", TextArea).text.strip()
            if not query:
                self.notify("Query is empty.", severity="warning")
                return
            try:
                columns, rows = self.manager.execute_query(query)
                csv_data = self.manager.export_csv(columns, rows)
                if not csv_data:
                    self.notify("No data to export.", severity="warning")
                else:
                    # Write to a temp file or just copy to clipboard / display
                    # Since we don't have direct clipboard access here without clipboard_lab, we'll display it
                    self.display_message(csv_data)
                    self.notify("Exported CSV data shown in output.")
            except Exception as e:
                self.notify(f"Export Error: {e}", severity="error")

    def display_data(self, columns: list, rows: list):
        """Displays data in the DataTable."""
        table = self.query_one("#sqlite-table", DataTable)
        table.clear(columns=True)
        if columns:
            table.add_columns(*columns)
        for row in rows:
            table.add_row(*[str(row.get(col, "")) for col in columns])

    def display_message(self, message: str):
        """Displays a single text message in the DataTable."""
        table = self.query_one("#sqlite-table", DataTable)
        table.clear(columns=True)
        table.add_column("Message")
        for line in message.splitlines():
            table.add_row(line)
