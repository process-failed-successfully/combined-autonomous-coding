from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, Input, Button, DataTable, Select, Checkbox, RichLog
from textual import on
from shared.find_lab import FindLabManager
import datetime

class FindLabTab(Container):
    """Tab for Advanced File Search."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = FindLabManager(project_dir)
        self.results = []

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Filters Pane
            with Vertical(id="find-filters-pane", classes="stat-box"):
                yield Label("[bold]Search Filters[/bold]")

                yield Label("Name (Glob):")
                yield Input(placeholder="*.py", id="find-name")

                yield Label("Regex:")
                yield Input(placeholder=".*model.*", id="find-regex")

                yield Label("Size (e.g. >1M, <10k):")
                yield Input(placeholder=">1M", id="find-size")

                yield Label("Time (e.g. >1d, <1h):")
                yield Input(placeholder="<24h", id="find-time")

                yield Label("Extensions (comma-sep):")
                yield Input(placeholder="py,md", id="find-ext")

                yield Label("Type:")
                yield Select.from_values(["Any", "File", "Directory", "Symlink"], id="find-type", value="Any")

                yield Button("Find", id="btn-find-run", variant="primary")

            # Results & Preview
            with Vertical(id="find-results-container"):
                yield Label("[bold]Results[/bold]")
                yield DataTable(id="find-table")

                yield Label("[bold]Preview / Actions[/bold]")
                with Horizontal(classes="stat-box"):
                    yield Button("Delete Selected", id="btn-find-delete", variant="error", disabled=True)
                    yield Label("", id="find-status-lbl")

                yield RichLog(id="find-preview-log", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        table = self.query_one("#find-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Path", "Size", "Modified", "Type")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-find-run":
            await self.run_search()
        elif event.button.id == "btn-find-delete":
            await self.delete_selected()

    async def run_search(self) -> None:
        name = self.query_one("#find-name", Input).value
        regex = self.query_one("#find-regex", Input).value
        size = self.query_one("#find-size", Input).value
        time_str = self.query_one("#find-time", Input).value
        ext = self.query_one("#find-ext", Input).value

        type_val = self.query_one("#find-type", Select).value
        type_map = {"File": "f", "Directory": "d", "Symlink": "l", "Any": None}
        type_char = type_map.get(type_val)

        table = self.query_one("#find-table", DataTable)
        table.clear()
        self.results = []
        self.query_one("#btn-find-delete").disabled = True
        self.query_one("#find-status-lbl").update("Searching...")

        import asyncio
        try:
            # Run in thread
            def do_find():
                return list(self.manager.find_files(
                    self.project_dir,
                    name_pattern=name,
                    regex_pattern=regex,
                    size_filter=size,
                    time_filter=time_str,
                    type_filter=type_char,
                    extensions=ext
                ))

            paths = await asyncio.to_thread(do_find)

            for p in paths:
                try:
                    stat = p.stat()
                    size_fmt = f"{stat.st_size:,} b"
                    mtime_fmt = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                    ptype = "Dir" if p.is_dir() else "Link" if p.is_symlink() else "File"

                    rel_path = str(p.relative_to(self.project_dir))
                    table.add_row(rel_path, size_fmt, mtime_fmt, ptype, key=str(p))
                    self.results.append(p)
                except Exception:
                    pass

            self.query_one("#find-status-lbl").update(f"Found {len(paths)} items.")

        except Exception as e:
            self.query_one("#find-status-lbl").update(f"Error: {e}")
            self.notify(f"Search error: {e}", severity="error")

    @on(DataTable.RowSelected, "#find-table")
    def on_row_selected(self, event: DataTable.RowSelected) -> None:
        self.query_one("#btn-find-delete").disabled = False
        path_str = event.row_key.value
        self.show_preview(Path(path_str))

    def show_preview(self, path: Path) -> None:
        log = self.query_one("#find-preview-log", RichLog)
        log.clear()

        log.write(f"[bold]{path}[/bold]")
        if path.is_file():
            try:
                # Read first 1kb
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read(1024)
                    log.write(content)
            except Exception as e:
                log.write(f"Error reading file: {e}")
        elif path.is_dir():
            log.write("(Directory)")

    @on(DataTable.RowSelected, "#find-table")
    def on_select_for_delete(self, event: DataTable.RowSelected) -> None:
        self.selected_path = Path(event.row_key.value)

    async def delete_selected(self) -> None:
        if not hasattr(self, "selected_path") or not self.selected_path:
            return

        p = self.selected_path

        # Confirmation (simplistic: toggle button label?)
        btn = self.query_one("#btn-find-delete", Button)
        if str(btn.label) != "Confirm Delete":
            btn.label = "Confirm Delete"
            btn.variant = "warning"
            return

        # Execute delete
        import asyncio
        import shutil
        try:
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()

            self.notify(f"Deleted {p.name}")
            # Remove from table
            table = self.query_one("#find-table", DataTable)
            table.remove_row(str(p))

            # Reset button
            btn.label = "Delete Selected"
            btn.variant = "error"
            btn.disabled = True
            self.selected_path = None
            self.query_one("#find-preview-log", RichLog).clear()

        except Exception as e:
            self.notify(f"Error deleting: {e}", severity="error")
