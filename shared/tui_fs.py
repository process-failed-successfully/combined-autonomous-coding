from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Label, DirectoryTree, Button, RichLog, Input, Select, Checkbox
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from shared.fs_lab import FsLabManager


class FsLabTab(Container):
    """
    TUI Tab for Fs Lab.
    """
    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = FsLabManager()
        self.selected_path = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left: Directory Tree
            with Vertical(id="fs-left-pane", classes="stat-box"):
                yield Label("[bold]File Explorer[/bold]")
                yield DirectoryTree(str(self.project_dir), id="fs-tree")
                yield Button("Refresh Tree", id="btn-fs-refresh-tree", variant="default")

            # Right: Details and Actions
            with VerticalScroll(id="fs-right-pane"):
                yield Label("[bold]File/Directory Operations[/bold]", classes="welcome-text")
                yield Label("Selected Path: None", id="lbl-fs-selected-path")

                # Info Section
                with Container(classes="stat-box"):
                    yield Label("[bold]Info & Usage[/bold]")
                    with Horizontal():
                        yield Button("Get Info", id="btn-fs-info", variant="primary", disabled=True)
                        yield Button("Get Usage (Tree)", id="btn-fs-usage", variant="primary", disabled=True)
                    yield RichLog(id="fs-info-log", wrap=True, highlight=True, markup=True)

                # Search Section
                with Container(classes="stat-box"):
                    yield Label("[bold]Find[/bold]")
                    with Horizontal():
                        yield Input(placeholder="Name (e.g. *.py)", id="fs-find-name", value="*")
                        yield Input(placeholder="Size (e.g. >10M)", id="fs-find-size")
                    with Horizontal():
                        yield Input(placeholder="MTime (e.g. >1d)", id="fs-find-mtime")
                        yield Select([("Any", ""), ("File", "f"), ("Directory", "d")], value="", id="fs-find-type")
                    yield Input(placeholder="Content regex", id="fs-find-content")
                    yield Button("Find", id="btn-fs-find", variant="warning", disabled=True)

                # Dedup, Clean, Shred Section
                with Container(classes="stat-box"):
                    yield Label("[bold]Maintenance[/bold]")
                    with Horizontal():
                        yield Checkbox("Dry Run", value=True, id="fs-chk-dry-run")
                        yield Checkbox("Delete Duplicates", value=False, id="fs-chk-del-dedup")
                    with Horizontal():
                        yield Button("Find Duplicates", id="btn-fs-dedup", variant="warning", disabled=True)
                        yield Button("Clean (Temp/Empty)", id="btn-fs-clean", variant="error", disabled=True)
                        yield Button("Shred File", id="btn-fs-shred", variant="error", disabled=True)
                        yield Input(placeholder="Passes", id="fs-shred-passes", value="3")

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        self.selected_path = event.path
        self._update_selected_path()

    def on_directory_tree_directory_selected(self, event: DirectoryTree.DirectorySelected) -> None:
        self.selected_path = event.path
        self._update_selected_path()

    def _update_selected_path(self):
        lbl = self.query_one("#lbl-fs-selected-path", Label)
        if self.selected_path:
            lbl.update(f"Selected Path: {self.selected_path.name}")
            self.query_one("#btn-fs-info").disabled = False
            self.query_one("#btn-fs-usage").disabled = False
            self.query_one("#btn-fs-find").disabled = False
            self.query_one("#btn-fs-dedup").disabled = False
            self.query_one("#btn-fs-clean").disabled = False
            self.query_one("#btn-fs-shred").disabled = not self.selected_path.is_file()
        else:
            lbl.update("Selected Path: None")
            self.query_one("#btn-fs-info").disabled = True
            self.query_one("#btn-fs-usage").disabled = True
            self.query_one("#btn-fs-find").disabled = True
            self.query_one("#btn-fs-dedup").disabled = True
            self.query_one("#btn-fs-clean").disabled = True
            self.query_one("#btn-fs-shred").disabled = True

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        log = self.query_one("#fs-info-log", RichLog)
        if event.button.id == "btn-fs-refresh-tree":
            self.query_one("#fs-tree", DirectoryTree).reload()
            self.selected_path = None
            self._update_selected_path()
            log.clear()

        elif event.button.id == "btn-fs-info":
            if not self.selected_path:
                return
            log.clear()
            try:
                info = self.manager.get_info(self.selected_path)
                log.write(f"[bold]Info for {info['name']}[/bold]")
                for k, v in info.items():
                    log.write(f"{k.replace('_', ' ').title()}: {v}")
            except Exception as e:
                log.write(f"[red]Error getting info: {e}[/red]")

        elif event.button.id == "btn-fs-usage":
            if not self.selected_path:
                return
            log.clear()
            # Usage outputs to Rich console, so we intercept it using a custom console or redirect stdout
            # Alternatively, we can just write simple text to RichLog
            import io
            from rich.console import Console
            string_io = io.StringIO()
            custom_console = Console(file=string_io, force_terminal=False)
            old_console = self.manager.console
            self.manager.console = custom_console
            try:
                self.manager.usage(self.selected_path, depth=1)
                log.write(string_io.getvalue())
            except Exception as e:
                log.write(f"[red]Error getting usage: {e}[/red]")
            finally:
                self.manager.console = old_console

        elif event.button.id == "btn-fs-find":
            if not self.selected_path:
                return
            log.clear()
            name = self.query_one("#fs-find-name", Input).value or "*"
            size = self.query_one("#fs-find-size", Input).value or None
            mtime = self.query_one("#fs-find-mtime", Input).value or None
            ftype = self.query_one("#fs-find-type", Select).value or None
            content = self.query_one("#fs-find-content", Input).value or None
            try:
                results = self.manager.find(self.selected_path, name=name, size=size, mtime=mtime, ftype=ftype, content=content)
                log.write(f"[bold]Found {len(results)} matches in {self.selected_path.name}:[/bold]")
                for p in results:
                    log.write(str(p))
            except Exception as e:
                log.write(f"[red]Error in find: {e}[/red]")

        elif event.button.id == "btn-fs-dedup":
            if not self.selected_path:
                return
            log.clear()
            delete = self.query_one("#fs-chk-del-dedup", Checkbox).value
            dry_run = self.query_one("#fs-chk-dry-run", Checkbox).value

            import io
            from rich.console import Console
            string_io = io.StringIO()
            custom_console = Console(file=string_io, force_terminal=False)
            old_console = self.manager.console
            self.manager.console = custom_console

            try:
                duplicates = self.manager.dedup(self.selected_path, delete=delete, dry_run=dry_run)
                log.write(string_io.getvalue())
                if not delete:
                    count = 0
                    for h, paths in duplicates.items():
                        log.write(f"Duplicate Group ({h[:8]}...):")
                        for p in paths:
                            log.write(f"  - {p}")
                        count += len(paths) - 1
                    log.write(f"\\nFound {len(duplicates)} groups with duplicates (approx {count} redundant files).")
            except Exception as e:
                log.write(f"[red]Error in dedup: {e}[/red]")
            finally:
                self.manager.console = old_console

        elif event.button.id == "btn-fs-clean":
            if not self.selected_path:
                return
            log.clear()
            dry_run = self.query_one("#fs-chk-dry-run", Checkbox).value
            try:
                import io
                import sys
                string_io = io.StringIO()
                old_stdout = sys.stdout
                sys.stdout = string_io
                stats = self.manager.clean(self.selected_path, dry_run=dry_run)
                sys.stdout = old_stdout
                log.write(string_io.getvalue())
                if dry_run:
                    log.write("\\n[yellow][Dry Run] Uncheck 'Dry Run' to actually delete.[/yellow]")
                log.write(f"\\nSummary:\\n  Files: {stats['files']}\\n  Dirs:  {stats['dirs']}\\n  Space: {self.manager._format_size(stats['space'])}")
            except Exception as e:
                sys.stdout = old_stdout
                log.write(f"[red]Error in clean: {e}[/red]")

        elif event.button.id == "btn-fs-shred":
            if not self.selected_path or not self.selected_path.is_file():
                return
            log.clear()
            passes_str = self.query_one("#fs-shred-passes", Input).value
            passes = int(passes_str) if passes_str and passes_str.isdigit() else 3
            try:
                success = self.manager.shred(self.selected_path, passes=passes)
                if success:
                    log.write(f"[green]Successfully shredded {self.selected_path}[/green]")
                    self.query_one("#fs-tree", DirectoryTree).reload()
                    self.selected_path = None
                    self._update_selected_path()
                else:
                    log.write(f"[red]Failed to shred {self.selected_path}[/red]")
            except Exception as e:
                log.write(f"[red]Error in shred: {e}[/red]")
