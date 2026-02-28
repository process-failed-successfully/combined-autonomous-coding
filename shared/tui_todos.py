from pathlib import Path
from typing import List, Any
import asyncio

from textual.app import ComposeResult
from textual.widgets import Label, DataTable, Button, Input, RichLog, Select
from textual.containers import Container, Horizontal, Vertical
from textual import on
from textual.worker import Worker, WorkerState

from shared.todo_lab import TodoLabManager
from shared.todos import DEFAULT_TAGS


class TodosLabTab(Container):
    """
    Interactive Todos Lab Tab.
    """
    def __init__(self, project_dir: Path, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = TodoLabManager(self.project_dir)
        self.todos: List[dict[str, Any]] = []
        self.filtered_todos: List[dict[str, Any]] = []

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left side: Todos Table and Controls
            with Vertical(id="todos-main", classes="stat-box"):
                yield Label("[bold]TODO List[/bold]", id="lbl-todos-title")

                with Horizontal(id="todos-controls"):
                    yield Button("Scan Codebase", id="btn-todos-scan", variant="primary")
                    yield Input(placeholder="Search text...", id="input-todos-search")

                    tags_options = [("All Tags", "ALL")] + [(tag, tag) for tag in DEFAULT_TAGS]
                    yield Select(tags_options, id="select-todos-tag", value="ALL", allow_blank=False)

                yield DataTable(id="table-todos", cursor_type="row")

            # Right side: Details
            with Vertical(id="todos-details", classes="stat-box"):
                yield Label("[bold]TODO Details[/bold]")
                yield RichLog(id="log-todos-details", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        table = self.query_one("#table-todos", DataTable)
        table.add_columns("File", "Line", "Tag", "Text", "Author", "Date")

    @on(Button.Pressed, "#btn-todos-scan")
    def on_scan_pressed(self) -> None:
        self.log_message("Scanning codebase for TODOs...")
        self.query_one("#btn-todos-scan", Button).disabled = True
        self.run_worker(self._scan_todos_worker(), thread=True)

    async def _scan_todos_worker(self) -> List[dict[str, Any]]:
        return await asyncio.to_thread(self.manager.get_todos_with_blame)

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.state == WorkerState.SUCCESS:
            if event.worker.result:
                self.todos = event.worker.result
            self.apply_filters()
            self.query_one("#btn-todos-scan", Button).disabled = False
            self.query_one("#lbl-todos-title", Label).update(f"[bold]TODO List[/bold] ({len(self.todos)} found)")
            self.log_message(f"[green]Scan complete! Found {len(self.todos)} TODOs.[/green]")
        elif event.state == WorkerState.ERROR:
            self.query_one("#btn-todos-scan", Button).disabled = False
            self.log_message(f"[red]Error scanning TODOs: {event.worker.error}[/red]")

    @on(Input.Changed, "#input-todos-search")
    def on_search_changed(self, event: Input.Changed) -> None:
        self.apply_filters()

    @on(Select.Changed, "#select-todos-tag")
    def on_tag_changed(self, event: Select.Changed) -> None:
        self.apply_filters()

    def apply_filters(self) -> None:
        search_text = self.query_one("#input-todos-search", Input).value.lower()
        selected_tag = self.query_one("#select-todos-tag", Select).value

        self.filtered_todos = []
        for todo in self.todos:
            # Check tag filter
            if selected_tag != "ALL" and todo["tag"] != selected_tag:
                continue

            # Check search text
            if search_text and search_text not in todo["text"].lower() and search_text not in todo["file"].lower():
                continue

            self.filtered_todos.append(todo)

        self.populate_table()

    def populate_table(self) -> None:
        table = self.query_one("#table-todos", DataTable)
        table.clear()

        for idx, todo in enumerate(self.filtered_todos):
            table.add_row(
                todo["file"],
                str(todo["line"]),
                todo["tag"],
                todo["text"],
                todo.get("author", "Unknown"),
                todo.get("date", "Unknown"),
                key=str(idx)
            )

    @on(DataTable.RowSelected, "#table-todos")
    def on_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.row_key.value:
            idx = int(event.row_key.value)
            if 0 <= idx < len(self.filtered_todos):
                todo = self.filtered_todos[idx]
                log = self.query_one("#log-todos-details", RichLog)
                log.clear()

                log.write(f"[bold]File:[/bold] {todo['file']}")
                log.write(f"[bold]Line:[/bold] {todo['line']}")
                log.write(f"[bold]Tag:[/bold] {todo['tag']}")
                log.write(f"[bold]Text:[/bold] {todo['text']}")
                log.write(f"[bold]Author:[/bold] {todo.get('author', 'Unknown')}")
                log.write(f"[bold]Date:[/bold] {todo.get('date', 'Unknown')}")

                # Try to show context if file exists
                file_path = self.project_dir / todo['file']
                if file_path.exists():
                    log.write("\n[bold]Context:[/bold]")
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            lines = f.readlines()
                            line_idx = todo['line'] - 1

                            start_idx = max(0, line_idx - 2)
                            end_idx = min(len(lines), line_idx + 3)

                            for i in range(start_idx, end_idx):
                                prefix = ">> " if i == line_idx else "   "
                                log.write(f"{prefix}{i+1:4d} | {lines[i].rstrip()}")
                    except Exception as e:
                        log.write(f"[red]Could not read file for context: {e}[/red]")

    def log_message(self, message: str) -> None:
        log = self.query_one("#log-todos-details", RichLog)
        log.write(message)
