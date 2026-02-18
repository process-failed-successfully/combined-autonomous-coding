from pathlib import Path
import asyncio
from textual.app import ComposeResult
from textual.widgets import Label, DataTable, Button, ListView, ListItem, TextArea, Input, Select, RichLog
from textual.containers import Container, Horizontal, Vertical
from textual import on
from shared.sql_lab import SqlLabManager, detect_connection_string
from shared.db_query import generate_sql

class DatabaseTab(Container):
    """
    Enhanced Database Management Tab.
    Supports table browsing, custom SQL execution, and AI query generation.
    """

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = None
        self.connection_string = None
        self.current_schema = ""

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: Connection & Tables
            with Vertical(id="db-sidebar", classes="stat-box"):
                yield Label("[bold]Database[/bold]")
                yield Label("Not Connected", id="lbl-db-conn")
                yield Button("Connect / Refresh", id="btn-db-connect", variant="primary")

                yield Label("[bold]Tables[/bold]")
                yield ListView(id="db-table-list")

            # Right Pane: Query & Results
            with Vertical(id="db-main"):
                # Query Controls
                with Horizontal(classes="stat-box", id="db-query-controls"):
                    yield Select.from_values(["SQL", "AI"], id="sel-query-mode", value="SQL")
                    yield Button("Execute", id="btn-db-run", variant="success")
                    yield Button("Clear", id="btn-db-clear", variant="default")

                # Query Editor
                yield TextArea(language="sql", id="input-db-query")

                # Results / Logs
                yield Label("[bold]Results[/bold]")
                yield DataTable(id="db-results-table")
                yield RichLog(id="db-log", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        table = self.query_one("#db-results-table", DataTable)
        table.cursor_type = "row"
        self.connect_db()

    def connect_db(self) -> None:
        self.connection_string = detect_connection_string(self.project_dir)
        lbl = self.query_one("#lbl-db-conn", Label)

        if self.connection_string:
            lbl.update(f"Connected: {self.connection_string}")
            self.manager = SqlLabManager(self.connection_string)
            self.load_tables()
            # Cache schema for AI
            try:
                self.current_schema = str(self.manager.get_schema())
            except Exception:
                self.current_schema = ""
        else:
            lbl.update("No DB found")
            self.notify("No database found.", severity="warning")

    def load_tables(self) -> None:
        list_view = self.query_one("#db-table-list", ListView)
        list_view.clear()

        if not self.manager:
            return

        tables = self.manager.list_tables()
        if not tables:
            list_view.append(ListItem(Label("No tables")))
            return

        for t in tables:
            list_view.append(ListItem(Label(t), name=t))

    @on(Button.Pressed, "#btn-db-connect")
    def on_connect_click(self) -> None:
        self.connect_db()
        self.notify("Database connection refreshed.")

    @on(Button.Pressed, "#btn-db-clear")
    def on_clear_click(self) -> None:
        self.query_one("#input-db-query", TextArea).text = ""
        self.query_one("#db-results-table", DataTable).clear(columns=True)
        self.query_one("#db-log", RichLog).clear()

    @on(Button.Pressed, "#btn-db-run")
    async def on_run_click(self) -> None:
        await self.run_query()

    @on(ListView.Selected, "#db-table-list")
    async def on_table_selected(self, event: ListView.Selected) -> None:
        if not event.item or not hasattr(event.item, "name") or not event.item.name:
            return

        # When table is clicked, generate a SELECT * query
        table_name = event.item.name
        query = f"SELECT * FROM {table_name} LIMIT 100"

        self.query_one("#sel-query-mode", Select).value = "SQL"
        self.query_one("#input-db-query", TextArea).text = query
        await self.run_query()

    async def run_query(self) -> None:
        if not self.manager:
            self.notify("Not connected to database.", severity="error")
            return

        query_input = self.query_one("#input-db-query", TextArea)
        query = query_input.text.strip()

        if not query:
            return

        mode = self.query_one("#sel-query-mode", Select).value
        log = self.query_one("#db-log", RichLog)
        log.clear()

        # Handle AI Mode
        if mode == "AI":
            log.write("[bold yellow]Generating SQL with AI...[/bold yellow]")
            try:
                # Use generate_sql from shared.db_query
                # We need to adapt it slightly or ensure it works with what we have
                sql = await generate_sql(query, self.current_schema, self.project_dir)
                if sql.startswith("ERROR:"):
                    log.write(f"[red]{sql}[/red]")
                    return

                log.write(f"Generated: [bold cyan]{sql}[/bold cyan]")
                query = sql
                query_input.text = sql
                self.query_one("#sel-query-mode", Select).value = "SQL"
            except Exception as e:
                log.write(f"[red]AI Error: {e}[/red]")
                return

        # Execute SQL
        log.write("Executing...")

        try:
            # Run in thread to allow UI updates
            def execute_safe():
                return self.manager.execute_query(query)

            result = await asyncio.to_thread(execute_safe)

            table = self.query_one("#db-results-table", DataTable)
            table.clear(columns=True)

            if not result["success"]:
                log.write(f"[bold red]Error:[/bold red] {result['error']}")
                self.notify("Query failed.", severity="error")
                return

            if "rows" in result:
                columns = result["columns"]
                rows = result["rows"]

                if columns:
                    table.add_columns(*columns)
                    # Convert row dicts to list of values
                    row_values = [[str(r.get(c, "")) for c in columns] for r in rows]
                    table.add_rows(row_values)

                log.write(f"[green]Success.[/green] {len(rows)} rows returned.")
            else:
                log.write(f"[green]Success.[/green] Rows affected: {result.get('rowcount', 0)}")

        except Exception as e:
            log.write(f"[bold red]Execution Error:[/bold red] {e}")
            self.notify(f"Error: {e}", severity="error")
