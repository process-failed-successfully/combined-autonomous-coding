import asyncio
import io
import contextlib
from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import DirectoryTree, RichLog, Label, Button, Checkbox, Input
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual import on

from shared.fs_lab import FsLabManager

class FsLabTab(Container):
    """Tab for FileSystem Lab utilities."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = FsLabManager()
        self.selected_path = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: File Tree
            with Vertical(id="fslab-left-pane", classes="stat-box"):
                yield Label("[bold]Select File/Directory[/bold]")
                yield DirectoryTree(str(self.project_dir), id="fslab-tree")

            # Right Pane: Controls & Output
            with Vertical(id="fslab-right-pane"):
                yield Label("[bold]FileSystem Operations[/bold]", classes="welcome-text")

                with Vertical(classes="stat-box"):
                    with Horizontal():
                        yield Button("Info", id="btn-fs-info", variant="primary", disabled=True)
                        yield Button("Find", id="btn-fs-find", variant="success")
                        yield Button("Usage", id="btn-fs-usage", variant="warning", disabled=True)
                        yield Button("Dedup", id="btn-fs-dedup", variant="error")
                        yield Button("Clean", id="btn-fs-clean", variant="error")

                    with Horizontal(id="fslab-shred-controls"):
                        yield Button("Shred", id="btn-fs-shred", variant="error", disabled=True)
                        yield Input(placeholder="Passes (e.g., 3)", id="input-fs-passes", value="3")
                        yield Checkbox("Dry Run", id="chk-fs-dry-run", value=True)

                yield Label("[bold]Output[/bold]")
                with VerticalScroll():
                    yield RichLog(id="fslab-log", wrap=True, highlight=True, markup=True)

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        self.selected_path = event.path
        self._enable_path_buttons()
        self.notify(f"Selected: {event.path.name}")

    def on_directory_tree_directory_selected(self, event: DirectoryTree.DirectorySelected) -> None:
        self.selected_path = event.path
        self._enable_path_buttons()
        self.notify(f"Selected Dir: {event.path.name}")

    def _enable_path_buttons(self) -> None:
        self.query_one("#btn-fs-info").disabled = False
        self.query_one("#btn-fs-usage").disabled = False
        # Shred only works on files
        if self.selected_path and self.selected_path.is_file():
            self.query_one("#btn-fs-shred").disabled = False
        else:
            self.query_one("#btn-fs-shred").disabled = True

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        log = self.query_one("#fslab-log", RichLog)

        if event.button.id == "btn-fs-info":
            if not self.selected_path:
                return
            log.clear()
            log.write(f"[bold]Info for: {self.selected_path}[/bold]")

            try:
                info = await asyncio.to_thread(self.manager.get_info, self.selected_path)
                for k, v in info.items():
                    log.write(f"  [cyan]{k}[/cyan]: {v}")
            except Exception as e:
                log.write(f"[red]Error:[/red] {e}")

        elif event.button.id == "btn-fs-find":
            log.clear()
            log.write(f"[bold]Finding files in {self.project_dir}...[/bold]")
            # Simplified find for TUI (can be expanded later with inputs)
            try:
                results = await asyncio.to_thread(self.manager.find, self.project_dir)
                log.write(f"Found {len(results)} files (showing up to 100):")
                for p in results[:100]:
                    log.write(f"  {p.relative_to(self.project_dir)}")
            except Exception as e:
                log.write(f"[red]Error:[/red] {e}")

        elif event.button.id == "btn-fs-usage":
            if not self.selected_path:
                return
            log.clear()
            log.write(f"[bold]Usage for: {self.selected_path}[/bold]")

            # FsLabManager's usage method prints to rich.console.
            # We capture it to a StringIO to write to RichLog.
            try:
                from rich.console import Console
                # FsLabManager allows passing a custom console, but we'll capture its default behavior if no console passed,
                # or we just re-create a temporary manager with a captured console.
                capture = io.StringIO()
                console = Console(file=capture, force_terminal=False)
                temp_manager = FsLabManager(console=console)

                await asyncio.to_thread(temp_manager.usage, self.selected_path, depth=2)

                log.write(capture.getvalue())
            except Exception as e:
                log.write(f"[red]Error:[/red] {e}")

        elif event.button.id == "btn-fs-dedup":
            log.clear()
            dry_run = self.query_one("#chk-fs-dry-run", Checkbox).value
            delete = not dry_run

            log.write(f"[bold]Deduplicating {self.project_dir}...[/bold]")
            if dry_run:
                log.write("[yellow](Dry Run - No files will be deleted)[/yellow]")
            else:
                log.write("[red](Deleting duplicates)[/red]")

            try:
                capture = io.StringIO()
                with contextlib.redirect_stdout(capture):
                    duplicates = await asyncio.to_thread(self.manager.dedup, self.project_dir, delete=delete, dry_run=dry_run)

                output = capture.getvalue()
                if output:
                    log.write(output)

                if not delete:
                    count = 0
                    for h, paths in duplicates.items():
                        log.write(f"Duplicate Group ({h[:8]}...):")
                        for p in paths:
                            log.write(f"  - {p}")
                        count += len(paths) - 1
                    log.write(f"\nFound {len(duplicates)} groups with duplicates (approx {count} redundant files).")
            except Exception as e:
                log.write(f"[red]Error:[/red] {e}")

        elif event.button.id == "btn-fs-clean":
            log.clear()
            dry_run = self.query_one("#chk-fs-dry-run", Checkbox).value

            log.write(f"[bold]Cleaning {self.project_dir}...[/bold]")
            if dry_run:
                log.write("[yellow](Dry Run - No files will be deleted)[/yellow]")
            else:
                log.write("[red](Deleting files)[/red]")

            try:
                capture = io.StringIO()
                with contextlib.redirect_stdout(capture):
                    stats = await asyncio.to_thread(self.manager.clean, self.project_dir, dry_run=dry_run)

                output = capture.getvalue()
                if output:
                    log.write(output)

                log.write("\n[bold]Summary:[/bold]")
                log.write(f"  Files: {stats['files']}")
                log.write(f"  Dirs:  {stats['dirs']}")
                log.write(f"  Space: {self.manager._format_size(stats['space'])}")
            except Exception as e:
                log.write(f"[red]Error:[/red] {e}")

        elif event.button.id == "btn-fs-shred":
            if not self.selected_path or not self.selected_path.is_file():
                return

            log.clear()
            dry_run = self.query_one("#chk-fs-dry-run", Checkbox).value
            passes_str = self.query_one("#input-fs-passes", Input).value
            try:
                passes = int(passes_str)
            except ValueError:
                passes = 3

            log.write(f"[bold]Shredding {self.selected_path}[/bold] (Passes: {passes})")

            if dry_run:
                log.write(f"[yellow]Would securely delete: {self.selected_path}[/yellow]")
            else:
                try:
                    success = await asyncio.to_thread(self.manager.shred, self.selected_path, passes=passes)
                    if success:
                        log.write(f"[green]Successfully shredded {self.selected_path}[/green]")
                        self.selected_path = None
                        self._enable_path_buttons()
                    else:
                        log.write(f"[red]Failed to shred {self.selected_path}[/red]")
                except Exception as e:
                    log.write(f"[red]Error:[/red] {e}")
