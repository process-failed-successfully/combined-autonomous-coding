from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, Button, Input, DataTable, DirectoryTree, TabbedContent, TabPane, RichLog
from textual import on
from shared.archive_lab import ArchiveLabManager
import sys

class ArchiveLabTab(Container):
    """Tab for managing archives (zip, tar)."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = ArchiveLabManager(project_dir)
        self.selected_archive = None

    def compose(self) -> ComposeResult:
        with TabbedContent():
            with TabPane("Inspect & Extract"):
                with Horizontal():
                    # Left Pane: Tree
                    with Vertical(classes="stat-box", id="archive-tree-pane"):
                        yield Label("Select Archive:")
                        yield DirectoryTree(str(self.project_dir), id="archive-tree")

                    # Right Pane: Content
                    with Vertical(classes="stat-box", id="archive-content-pane"):
                        yield Label("Contents:", id="lbl-archive-name")
                        yield DataTable(id="archive-table")

                        with Horizontal():
                            yield Input(placeholder="Extract destination (optional)...", id="extract-dest")
                            yield Button("Extract", id="btn-extract", variant="primary", disabled=True)

                        yield RichLog(id="archive-log", highlight=True, markup=True)

            with TabPane("Create Archive"):
                with Vertical(classes="stat-box"):
                    yield Label("Create New Archive")
                    yield Input(placeholder="Archive name (e.g. backup.zip)...", id="create-name")
                    yield Label("Files/Dirs to include (comma separated relative paths):")
                    yield Input(placeholder="src/, README.md", id="create-files")
                    yield Button("Create", id="btn-create", variant="success")
                    yield RichLog(id="create-log", highlight=True, markup=True)

    def on_mount(self) -> None:
        table = self.query_one("#archive-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Size", "Type", "Modified", "Name")

    @on(DirectoryTree.FileSelected, "#archive-tree")
    def on_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        path = event.path
        if not path.is_file():
            return

        # Check extension
        valid_exts = {'.zip', '.tar', '.gz', '.tgz', '.bz2', '.tbz', '.xz', '.txz'}
        # Check if suffix is valid or part of compound suffix
        is_valid = path.suffix in valid_exts or (len(path.suffixes) > 1 and path.suffixes[-1] in valid_exts)

        if is_valid:
            self.selected_archive = path
            self.load_archive_contents(path)
            self.query_one("#btn-extract").disabled = False
            self.query_one("#lbl-archive-name").update(f"Contents: {path.name}")
        else:
            self.query_one("#archive-log", RichLog).write(f"[yellow]Selected file {path.name} is not a recognized archive.[/yellow]")

    def load_archive_contents(self, path: Path) -> None:
        table = self.query_one("#archive-table", DataTable)
        table.clear()
        log = self.query_one("#archive-log", RichLog)
        log.clear()

        try:
            contents = self.manager.list_contents(path)
            for item in contents:
                size_str = self.manager.format_bytes(item['size'])
                mtime = item['modified'][:19].replace("T", " ")
                table.add_row(
                    size_str,
                    item['type'],
                    mtime,
                    item['name']
                )
            log.write(f"Loaded {len(contents)} items.")
        except Exception as e:
            log.write(f"[red]Error reading archive: {e}[/red]")
            table.clear()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-extract":
            await self.extract_archive()
        elif event.button.id == "btn-create":
            await self.create_archive()

    async def extract_archive(self) -> None:
        if not self.selected_archive:
            return

        dest_input = self.query_one("#extract-dest", Input).value
        log = self.query_one("#archive-log", RichLog)

        dest_path = None
        if dest_input:
            # Ensure path is relative to avoid escaping project_dir via absolute paths
            safe_dest = dest_input.lstrip("/")
            dest_path = self.project_dir / safe_dest

        log.write(f"Extracting {self.selected_archive.name}...")

        import asyncio
        try:
            out = await asyncio.to_thread(self.manager.extract, self.selected_archive, dest_path)
            log.write(f"[green]Successfully extracted to: {out}[/green]")
            self.notify("Extraction complete.")
        except Exception as e:
            log.write(f"[red]Extraction failed: {e}[/red]")
            self.notify("Extraction failed.", severity="error")

    async def create_archive(self) -> None:
        name_input = self.query_one("#create-name", Input).value
        files_input = self.query_one("#create-files", Input).value
        log = self.query_one("#create-log", RichLog)

        if not name_input or not files_input:
            self.notify("Name and files required.", severity="error")
            return

        # Ensure archive path is relative
        safe_name = name_input.lstrip("/")
        archive_path = self.project_dir / safe_name

        # Files are also relative
        files = []
        for f in files_input.split(","):
            f = f.strip()
            if not f: continue
            safe_f = f.lstrip("/")
            files.append(self.project_dir / safe_f)

        log.write(f"Creating archive {name_input}...")

        import asyncio
        try:
            out = await asyncio.to_thread(self.manager.create, archive_path, files)
            log.write(f"[green]Successfully created: {out}[/green]")
            self.notify("Archive created.")

            # Refresh tree if possible, though DirectoryTree auto-refreshes on filesystem events usually
            # But we can force it if needed? No explicit reload method exposed easily.
        except Exception as e:
            log.write(f"[red]Creation failed: {e}[/red]")
            self.notify("Creation failed.", severity="error")
