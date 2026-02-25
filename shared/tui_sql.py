from pathlib import Path
import asyncio
import contextlib
import io
from typing import Optional, List, Dict, Any
from textual.app import ComposeResult
from textual.widgets import Label, Input, Button, ListView, ListItem, TextArea, RichLog, DataTable, TabbedContent, TabPane, Select
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual import on
from shared.sql_lab import SqlLabManager, detect_connection_string
from shared.db_query import generate_sql

class SqlLabTab(Container):
    """
    SQL Lab Tab.
    Run SQL queries, inspect schema, and export results.
    """

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager: Optional[SqlLabManager] = None
        self.history: List[str] = []

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: Connection & Tables
            with Vertical(id="sql-sidebar", classes="stat-box"):
                yield Label("[bold]Database[/bold]")

                # Connection
                yield Label("Connection String:")
                yield Input(placeholder="sqlite:///agent_lab.db", id="sql-url-input")
                yield Button("Connect", id="btn-sql-connect", variant="primary")
                yield Label("Not Connected", id="lbl-sql-status", classes="status-text")

                # AI Assistant
                yield Label("[bold]AI Assistant[/bold]")
                yield Input(placeholder="Ask a question...", id="sql-ai-input")
                yield Select.from_values(["gemini", "cursor", "local"], id="sql-ai-agent", value="gemini")
                yield Button("Generate SQL", id="btn-sql-ai-generate", variant="warning", disabled=True)

                # Tables
                yield Label("[bold]Tables[/bold]")
                yield Button("Refresh Tables", id="btn-sql-refresh-tables", variant="default", disabled=True)
                yield ListView(id="sql-table-list")

            # Right Pane: Query & Results
            with Vertical(id="sql-main"):
                # Query Editor
                with Vertical(classes="stat-box", id="sql-query-container"):
                    yield Label("[bold]Query Editor[/bold]")
                    yield TextArea(id="sql-query-editor", language="sql")
                    with Horizontal():
                        yield Button("Execute", id="btn-sql-execute", variant="success", disabled=True)
                        yield Button("Clear", id="btn-sql-clear", variant="error")

                # Results
                with VerticalScroll(classes="stat-box", id="sql-results-container"):
                    with TabbedContent(id="sql-results-tabs"):
                        with TabPane("Results", id="tab-sql-results"):
                            yield Label("", id="sql-result-info")
                            yield DataTable(id="sql-results-table")
                        with TabPane("Schema", id="tab-sql-schema"):
                            yield RichLog(id="sql-schema-log", wrap=True, markup=True)
                        with TabPane("Log", id="tab-sql-log"):
                            yield RichLog(id="sql-log", wrap=True, markup=True)

    def on_mount(self) -> None:
        # Detect connection string
        url = detect_connection_string(self.project_dir)
        if url:
            self.query_one("#sql-url-input", Input).value = url

        # Init DataTable
        table = self.query_one("#sql-results-table", DataTable)
        table.cursor_type = "row"

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-sql-connect":
            await self.connect_db()
        elif event.button.id == "btn-sql-refresh-tables":
            await self.load_tables()
        elif event.button.id == "btn-sql-execute":
            await self.execute_query()
        elif event.button.id == "btn-sql-clear":
            self.query_one("#sql-query-editor", TextArea).text = ""
        elif event.button.id == "btn-sql-ai-generate":
            await self.generate_ai_query()

    async def connect_db(self) -> None:
        url = self.query_one("#sql-url-input", Input).value
        if not url:
            self.notify("Connection string required.", severity="error")
            return

        self.log_message(f"Connecting to {url}...")
        self.query_one("#lbl-sql-status", Label).update("Connecting...")

        try:
            # Init manager
            self.manager = SqlLabManager(url)

            # Test connection by listing tables (running in thread)
            def test_conn():
                if self.manager.engine:
                    try:
                        with self.manager.engine.connect() as conn:
                            return True
                    except Exception:
                        return False
                return False

            success = await asyncio.to_thread(test_conn)

            if success:
                self.query_one("#lbl-sql-status", Label).update("[green]Connected[/green]")
                self.notify("Connected to database.")

                # Enable buttons
                self.query_one("#btn-sql-refresh-tables").disabled = False
                self.query_one("#btn-sql-execute").disabled = False
                self.query_one("#btn-sql-ai-generate").disabled = False

                await self.load_tables()
            else:
                 self.query_one("#lbl-sql-status", Label).update("[red]Connection Failed[/red]")
                 self.notify("Connection failed.", severity="error")

        except Exception as e:
            self.query_one("#lbl-sql-status", Label).update("[red]Connection Failed[/red]")
            self.log_message(f"[red]Error: {e}[/red]")
            self.notify(f"Connection failed: {e}", severity="error")

    async def load_tables(self) -> None:
        if not self.manager:
            return

        list_view = self.query_one("#sql-table-list", ListView)
        list_view.clear()

        try:
            tables = await asyncio.to_thread(self.manager.list_tables)
            for t in tables:
                list_view.append(ListItem(Label(t), name=t))
            self.log_message(f"Loaded {len(tables)} tables.")
        except Exception as e:
            self.log_message(f"[red]Error loading tables: {e}[/red]")

    @on(ListView.Selected, "#sql-table-list")
    async def on_table_selected(self, event: ListView.Selected) -> None:
        # Ensure we have a valid item with name
        if event.item and hasattr(event.item, "name") and event.item.name:
            table_name = event.item.name
            await self.show_schema(table_name)

            # Simple select query
            self.query_one("#sql-query-editor", TextArea).text = f"SELECT * FROM {table_name} LIMIT 10;"  # nosec B608

    async def show_schema(self, table_name: str) -> None:
        if not self.manager:
            return

        log = self.query_one("#sql-schema-log", RichLog)
        log.clear()

        try:
            schema = await asyncio.to_thread(self.manager.get_schema, table_name)
            if not schema:
                log.write("No schema found.")
                return

            columns = schema.get(table_name, [])
            log.write(f"[bold]Schema for {table_name}[/bold]")

            from rich.table import Table
            t = Table(show_header=True)
            t.add_column("Column")
            t.add_column("Type")
            t.add_column("Nullable")
            t.add_column("Default")

            for col in columns:
                t.add_row(
                    col["name"],
                    col["type"],
                    str(col["nullable"]),
                    str(col["default"])
                )

            log.write(t)

            # Switch to schema tab
            self.query_one("#sql-results-tabs", TabbedContent).active = "tab-sql-schema"

        except Exception as e:
            log.write(f"[red]Error: {e}[/red]")

    async def execute_query(self) -> None:
        if not self.manager:
            self.notify("Not connected.", severity="warning")
            return

        query = self.query_one("#sql-query-editor", TextArea).text
        if not query:
            self.notify("Query empty.", severity="warning")
            return

        self.log_message(f"Executing: {query}")
        self.notify("Executing query...")

        try:
            result = await asyncio.to_thread(self.manager.execute_query, query)

            if result.get("success"):
                self.notify("Query executed successfully.")
                self.display_results(result)
            else:
                self.notify("Query failed.", severity="error")
                self.log_message(f"[red]Error: {result.get('error')}[/red]")

        except Exception as e:
             self.notify(f"Execution error: {e}", severity="error")
             self.log_message(f"[red]Exception: {e}[/red]")

    async def generate_ai_query(self) -> None:
        if not self.manager:
            self.notify("Not connected.", severity="warning")
            return

        question = self.query_one("#sql-ai-input", Input).value
        if not question:
            self.notify("Please ask a question.", severity="warning")
            return

        agent_type = self.query_one("#sql-ai-agent", Select).value or "gemini"

        self.notify(f"Asking {agent_type}...", severity="information")
        self.log_message(f"Generating SQL for: {question}")

        try:
            # 1. Get Schema
            # We need to format the schema for the AI
            schema_dict = await asyncio.to_thread(self.manager.get_schema)
            schema_str = ""
            for table, columns in schema_dict.items():
                schema_str += f"Table: {table}\n"
                for col in columns:
                    schema_str += f"  - {col['name']} ({col['type']})\n"
                schema_str += "\n"

            # 2. Call AI
            sql = await generate_sql(question, schema_str, self.project_dir, agent_type=agent_type)

            if sql.startswith("ERROR:"):
                self.log_message(f"[red]{sql}[/red]")
                self.notify("AI failed to generate SQL.", severity="error")
            else:
                self.query_one("#sql-query-editor", TextArea).text = sql
                self.notify("SQL Generated.")
                self.log_message("[green]SQL generated from natural language.[/green]")

        except Exception as e:
            self.notify(f"AI Error: {e}", severity="error")
            self.log_message(f"[red]AI Error: {e}[/red]")

    def display_results(self, result: Dict[str, Any]) -> None:
        table = self.query_one("#sql-results-table", DataTable)
        table.clear(columns=True)

        if "rows" in result and result["rows"]:
            columns = result["columns"]
            rows = result["rows"]

            table.add_columns(*columns)
            for row in rows:
                # Convert row dict to list in correct order
                row_data = [str(row.get(c, "")) for c in columns]
                table.add_row(*row_data)

            self.query_one("#sql-result-info", Label).update(f"{len(rows)} rows returned.")
        else:
            msg = result.get("message", "Query executed.")
            rowcount = result.get("rowcount", 0)
            self.query_one("#sql-result-info", Label).update(f"{msg} (Rows affected: {rowcount})")

        # Switch to results tab
        self.query_one("#sql-results-tabs", TabbedContent).active = "tab-sql-results"

    def log_message(self, msg: str) -> None:
        self.query_one("#sql-log", RichLog).write(msg)
