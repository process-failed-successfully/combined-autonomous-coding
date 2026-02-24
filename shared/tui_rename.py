from pathlib import Path
from typing import List, Tuple
from textual.app import ComposeResult
from textual.widgets import Label, Button, Input, DataTable, DirectoryTree, Select, Checkbox
from textual.containers import Container, Horizontal, Vertical
from textual import on
import asyncio

from shared.rename_lab import RenameLabManager


class RenameLabTab(Container):
    """Tab for Batch Renaming Files."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = RenameLabManager()
        self.current_path = project_dir
        self.renames: List[Tuple[Path, Path]] = []

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: File Tree
            with Vertical(id="rename-tree-container", classes="stat-box"):
                yield Label("[bold]Select Directory[/bold]")
                yield DirectoryTree(str(self.project_dir), id="rename-dir-tree")

            # Right Pane: Controls & Preview
            with Vertical(id="rename-main-container"):
                yield Label("[bold]Rename Configuration[/bold]")

                with Vertical(classes="stat-box"):
                    yield Label("Filter (Glob):")
                    yield Input(value="*", placeholder="e.g. *.py", id="rename-glob")

                    yield Label("Search Pattern (Regex):")
                    yield Input(placeholder="e.g. ^test_(.*)", id="rename-search")

                    yield Label("Replacement:")
                    yield Input(placeholder="e.g. \\1_test", id="rename-replace")

                    yield Label("Transform:")
                    yield Select.from_values(
                        ["None", "upper", "lower", "title", "camel", "snake", "kebab", "dot", "path"],
                        id="rename-transform",
                        value="None"
                    )

                    with Horizontal():
                        yield Checkbox("Recursive", id="rename-recursive")
                        yield Button("Preview", id="btn-rename-preview", variant="primary")
                        yield Button("Apply", id="btn-rename-apply", variant="error", disabled=True)

                yield Label("[bold]Preview[/bold]")
                yield DataTable(id="rename-table")

    def on_mount(self) -> None:
        table = self.query_one("#rename-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Original", "New Name", "Status")

    def on_directory_tree_directory_selected(self, event: DirectoryTree.DirectorySelected) -> None:
        self.current_path = event.path
        self.notify(f"Selected: {self.current_path.name}")

    @on(Button.Pressed, "#btn-rename-preview")
    async def on_preview(self) -> None:
        await self.update_preview()

    @on(Button.Pressed, "#btn-rename-apply")
    async def on_apply(self) -> None:
        if not self.renames:
            self.notify("No renames to apply.", severity="warning")
            return

        self.notify("Applying renames...")

        def do_apply():
            # Apply renames (synchronous)
            return self.manager.apply_renames(self.renames, dry_run=False)

        try:
            success = await asyncio.to_thread(do_apply)
            if success:
                self.notify(f"Successfully renamed {len(self.renames)} files.")
                self.renames = []
                self.query_one("#btn-rename-apply").disabled = True
                # Refresh preview to show empty/done
                await self.update_preview()
            else:
                self.notify("Rename operation failed. Check logs.", severity="error")
        except Exception as e:
            self.notify(f"Error applying renames: {e}", severity="error")

    async def update_preview(self) -> None:
        glob_pattern = self.query_one("#rename-glob", Input).value or "*"
        search_pattern = self.query_one("#rename-search", Input).value
        replace_pattern = self.query_one("#rename-replace", Input).value
        transform_val = self.query_one("#rename-transform", Select).value
        recursive = self.query_one("#rename-recursive", Checkbox).value

        transform = transform_val if transform_val != "None" else None

        self.notify("Calculating preview...")
        table = self.query_one("#rename-table", DataTable)
        table.clear()

        def calculate():
            files = self.manager.find_files(self.current_path, glob_pattern, recursive=recursive)
            return self.manager.calculate_renames(
                files,
                search=search_pattern,
                replace=replace_pattern,
                transform=transform
            )

        try:
            self.renames = await asyncio.to_thread(calculate)

            if not self.renames:
                self.notify("No matching files found or no changes needed.")
                self.query_one("#btn-rename-apply").disabled = True
                return

            self.notify(f"Found {len(self.renames)} files to rename.")

            for src, dest in self.renames:
                status = "[green]Ready[/green]"
                if dest.exists():
                    status = "[red]Conflict[/red]"

                table.add_row(src.name, dest.name, status)

            # Enable apply only if renames exist
            self.query_one("#btn-rename-apply").disabled = False

        except Exception as e:
            self.notify(f"Error calculating preview: {e}", severity="error")
