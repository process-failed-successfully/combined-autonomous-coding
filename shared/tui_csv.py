from pathlib import Path
from typing import List, Dict, Any, Optional
from textual.app import ComposeResult
from textual.widgets import Label, DirectoryTree, DataTable, Input, Button, RichLog
from textual.containers import Container, Horizontal, Vertical
from textual import on
from shared.csv_lab import CsvLabManager

class CsvLabTab(Container):
    """
    Interactive CSV Editor Tab.
    """
    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = CsvLabManager(project_dir)
        self.current_file: Optional[Path] = None
        self.current_data: List[Dict[str, Any]] = []
        self.current_headers: List[str] = []
        self.selected_cell: Optional[tuple] = None # (row_key, col_key)

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left: File Browser
            with Vertical(id="csv-sidebar", classes="stat-box"):
                yield Label("[bold]CSV Files[/bold]")
                yield DirectoryTree(str(self.project_dir), id="csv-file-tree")

            # Center: Table
            with Vertical(id="csv-main"):
                yield Label("[bold]Table View[/bold]", id="lbl-csv-file")
                yield DataTable(id="csv-table")

            # Right: Editor & Actions
            with Vertical(id="csv-editor-pane", classes="stat-box"):
                yield Label("[bold]Cell Editor[/bold]")

                yield Label("Selected Cell:")
                yield Label("None", id="lbl-selected-cell")

                yield Label("Value:")
                yield Input(id="csv-cell-input", disabled=True)

                yield Button("Update Cell", id="btn-csv-update", variant="primary", disabled=True)

                yield Label("[bold]Actions[/bold]")
                yield Button("Save File", id="btn-csv-save", variant="success", disabled=True)
                yield Button("Add Row", id="btn-csv-add-row", variant="default", disabled=True)
                yield Button("Delete Row", id="btn-csv-del-row", variant="error", disabled=True)

                yield RichLog(id="csv-log", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        table = self.query_one("#csv-table", DataTable)
        table.cursor_type = "cell"

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        path = event.path
        if path.suffix.lower() == ".csv":
            self.load_file(path)
        else:
            self.notify("Please select a .csv file.", severity="warning")

    def load_file(self, path: Path) -> None:
        self.current_file = path
        try:
            self.current_data = self.manager.load_csv(path)
            self.current_headers = self.manager.get_headers(self.current_data)

            self.query_one("#lbl-csv-file", Label).update(f"[bold]File: {path.name}[/bold]")
            self.populate_table()

            # Enable buttons
            self.query_one("#btn-csv-save").disabled = False
            self.query_one("#btn-csv-add-row").disabled = False

            self.log_message(f"Loaded {path.name} ({len(self.current_data)} rows)")

        except Exception as e:
            self.log_message(f"[red]Error loading CSV: {e}[/red]")
            self.current_data = []
            self.query_one("#csv-table", DataTable).clear(columns=True)

    def populate_table(self) -> None:
        table = self.query_one("#csv-table", DataTable)
        table.clear(columns=True)

        if not self.current_headers:
            return

        # Add columns
        for h in self.current_headers:
            table.add_column(h, key=h)

        # Add rows
        for i, row in enumerate(self.current_data):
            # We use row index as key for easy mapping
            row_values = [str(row.get(h, "")) for h in self.current_headers]
            table.add_row(*row_values, key=str(i))

    @on(DataTable.CellSelected, "#csv-table")
    def on_cell_selected(self, event: DataTable.CellSelected) -> None:
        row_key = event.row_key.value
        col_key = event.column_key.value
        self.selected_cell = (row_key, col_key)

        value = str(event.value)

        self.query_one("#lbl-selected-cell", Label).update(f"Row {row_key}, Col '{col_key}'")

        inp = self.query_one("#csv-cell-input", Input)
        inp.disabled = False
        inp.value = value

        self.query_one("#btn-csv-update").disabled = False
        self.query_one("#btn-csv-del-row").disabled = False

    @on(Button.Pressed, "#btn-csv-update")
    def on_update_cell(self) -> None:
        if not self.selected_cell:
            return

        row_idx_str, col_key = self.selected_cell
        new_value = self.query_one("#csv-cell-input", Input).value

        try:
            row_idx = int(row_idx_str)
            # Update in-memory data
            if 0 <= row_idx < len(self.current_data):
                self.current_data[row_idx][col_key] = new_value

                # Update UI
                table = self.query_one("#csv-table", DataTable)
                table.update_cell(row_idx_str, col_key, new_value)

                self.log_message(f"Updated cell {row_idx}:{col_key}")
            else:
                self.log_message("[red]Row index out of range.[/red]")

        except Exception as e:
            self.log_message(f"[red]Error updating cell: {e}[/red]")

    @on(Button.Pressed, "#btn-csv-save")
    def on_save(self) -> None:
        if not self.current_file:
            return

        try:
            self.manager.save_csv(self.current_data, self.current_file)
            self.log_message(f"[green]Saved to {self.current_file.name}[/green]")
        except Exception as e:
            self.log_message(f"[red]Error saving file: {e}[/red]")

    @on(Button.Pressed, "#btn-csv-add-row")
    def on_add_row(self) -> None:
        if not self.current_headers:
            return

        # Create empty row
        new_row = {h: "" for h in self.current_headers}
        self.current_data.append(new_row)

        # Update Table
        table = self.query_one("#csv-table", DataTable)
        idx = len(self.current_data) - 1
        row_values = ["" for _ in self.current_headers]
        table.add_row(*row_values, key=str(idx))

        self.log_message(f"Added row {idx}")

    @on(Button.Pressed, "#btn-csv-del-row")
    def on_del_row(self) -> None:
        if not self.selected_cell:
            self.notify("Select a cell to identify the row to delete.", severity="warning")
            return

        row_idx_str, _ = self.selected_cell
        try:
            row_idx = int(row_idx_str)
            if 0 <= row_idx < len(self.current_data):
                # Remove from data
                del self.current_data[row_idx]

                # Re-render table completely (simplest way to handle index shifts)
                # Alternatively, we could delete row from table, but subsequent row keys won't match indices in self.current_data
                # So re-populating is safer for consistency.
                self.populate_table()

                self.selected_cell = None
                self.query_one("#csv-cell-input", Input).value = ""
                self.query_one("#csv-cell-input", Input).disabled = True
                self.query_one("#btn-csv-update").disabled = True
                self.query_one("#btn-csv-del-row").disabled = True
                self.query_one("#lbl-selected-cell", Label).update("None")

                self.log_message(f"Deleted row {row_idx}")
        except Exception as e:
            self.log_message(f"[red]Error deleting row: {e}[/red]")

    def log_message(self, message: str) -> None:
        log = self.query_one("#csv-log", RichLog)
        log.write(message)
