import json
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, Label, DataTable, Tree, TabPane
from textual.reactive import reactive
from textual.binding import Binding
from textual import work

from shared.mysql_lab import MysqlLabManager

class MysqlLabTab(TabPane):
    """Tab for MySQL Lab experimentation."""

    BINDINGS = [
        Binding("ctrl+r", "run_query", "Run Query", show=True),
    ]

    uri_value = reactive("mysql://root:root@localhost:3306/mysql")

    def __init__(self, id="tab-mysql", **kwargs):
        super().__init__("MySQL Lab", id=id, **kwargs)
        self.manager = None

    def compose(self) -> ComposeResult:
        yield Label("[bold]MySQL Lab[/bold]", classes="welcome-text")

        with Horizontal(id="mysql-connection-bar"):
            yield Input(placeholder="MySQL URI...", value=self.uri_value, id="mysql-uri", classes="flex-1")
            yield Button("Connect", id="mysql-connect-btn", variant="primary")

        yield Label("", id="mysql-status")

        with Horizontal(id="mysql-main-area"):
            with Vertical(id="mysql-sidebar", classes="w-1-3"):
                yield Label("[bold]Schema Explorer[/bold]")
                yield Tree("Database", id="mysql-schema-tree")
                yield Button("Refresh Schema", id="mysql-refresh-btn")

            with Vertical(id="mysql-workspace", classes="w-2-3"):
                yield Label("[bold]Query Editor[/bold]")
                yield Input(placeholder="SELECT * FROM ...", id="mysql-query-input")
                yield Button("Run Query", id="mysql-run-btn", variant="success")

                yield Label("[bold]Results[/bold]")
                yield DataTable(id="mysql-results-table", cursor_type="row")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "mysql-connect-btn":
            self.uri_value = str(self.query_one("#mysql-uri", Input).value)
            self.connect_to_db()
        elif button_id == "mysql-refresh-btn":
            self.refresh_schema()
        elif button_id == "mysql-run-btn":
            self.action_run_query()

    @work(exclusive=True, thread=True)
    def connect_to_db(self) -> None:
        try:
            self.manager = MysqlLabManager(uri=self.uri_value)
            self.manager.connect()
            self.app.call_from_thread(self.update_status, "Connected successfully!", "success")
            self.app.call_from_thread(self.refresh_schema)
        except Exception as e:
            self.app.call_from_thread(self.update_status, f"Connection failed: {e}", "error")

    def update_status(self, message: str, status_type: str = "info") -> None:
        status_label = self.query_one("#mysql-status", Label)
        color = "green" if status_type == "success" else "red" if status_type == "error" else "yellow"
        status_label.update(f"[{color}]{message}[/]")

    @work(exclusive=True, thread=True)
    def refresh_schema(self) -> None:
        if not self.manager:
            self.app.call_from_thread(self.update_status, "Not connected to a database.", "error")
            return

        try:
            tables = self.manager.get_tables()
            self.app.call_from_thread(self._populate_tree, tables)
            self.app.call_from_thread(self.update_status, "Schema refreshed.", "success")
        except Exception as e:
            self.app.call_from_thread(self.update_status, f"Failed to fetch schema: {e}", "error")

    def _populate_tree(self, tables: list[str]) -> None:
        tree = self.query_one("#mysql-schema-tree", Tree)
        tree.clear()
        root = tree.root
        root.expand()

        for table in tables:
            root.add(table)

    def action_run_query(self) -> None:
        if not self.manager:
            self.update_status("Not connected to a database.", "error")
            return

        query = str(self.query_one("#mysql-query-input", Input).value)
        if not query:
            return

        self.update_status("Running query...", "info")
        self.execute_query_worker(query)

    @work(exclusive=True, thread=True)
    def execute_query_worker(self, query: str) -> None:
        try:
            columns, rows = self.manager.execute_query(query)
            self.app.call_from_thread(self._render_results, columns, rows)
            self.app.call_from_thread(self.update_status, f"Query executed successfully ({len(rows)} rows).", "success")
        except Exception as e:
            self.app.call_from_thread(self.update_status, f"Query failed: {e}", "error")

    def _render_results(self, columns: list[str], rows: list[dict]) -> None:
        table = self.query_one("#mysql-results-table", DataTable)
        table.clear(columns=True)
        table.add_columns(*columns)

        for row in rows:
            row_data = [str(row.get(col, "")) for col in columns]
            table.add_row(*row_data)
