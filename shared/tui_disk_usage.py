import asyncio
from pathlib import Path
from typing import Any

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, Button, Tree, DataTable, Static
from textual import on

from shared.disk_usage import scan_disk_usage, format_size, get_largest_files
from shared.trash import TrashManager

class DiskUsageTab(Container):
    """Tab for visualizing disk usage."""

    def __init__(self, project_dir: Path, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.scan_data: dict = {}
        self.selected_path: Path | None = None
        self.trash_manager = TrashManager(project_dir)

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: Tree View
            with Vertical(id="du-tree-container", classes="stat-box"):
                yield Label("[bold]Directory Tree (Size)[/bold]")
                yield Tree("Scanning...", id="du-tree")
                yield Button("Refresh", id="btn-du-refresh", variant="default")

            # Right Pane: Top Files & Actions
            with Vertical(id="du-details-container"):
                yield Label("[bold]Largest Files[/bold]")
                yield DataTable(id="du-table")

                with Vertical(classes="stat-box"):
                    yield Label("[bold]Actions[/bold]")
                    yield Label("Select an item to see actions.", id="du-selected-lbl")
                    yield Button("Move to Trash", id="btn-du-delete", variant="warning", disabled=True)

    def on_mount(self) -> None:
        table = self.query_one("#du-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Size", "File Path")

        self.start_scan()

    def start_scan(self) -> None:
        self.query_one("#du-tree", Tree).root.label = "Scanning..."
        self.notify("Scanning disk usage...")
        asyncio.create_task(self._scan_task())

    async def _scan_task(self) -> None:
        # Run scan in thread
        self.scan_data = await asyncio.to_thread(scan_disk_usage, self.project_dir)
        largest_files = await asyncio.to_thread(get_largest_files, self.project_dir)

        # Update UI
        self._update_tree(self.scan_data)
        self._update_table(largest_files)
        self.notify("Scan complete.")

    def _update_tree(self, data: dict) -> None:
        tree = self.query_one("#du-tree", Tree)
        tree.clear()

        root_size = format_size(data.get("size", 0))
        root_label = f"{self.project_dir.name} ({root_size})"
        tree.root.label = root_label
        tree.root.data = data
        tree.root.expand()

        self._add_children(tree.root, data.get("children", []))

    def _add_children(self, node: Any, children: list) -> None:
        for child in children:
            size_str = format_size(child["size"])
            label = f"{child['name']} ({size_str})"

            # Allow expanding directories
            allow_expand = child["type"] == "dir"

            child_node = node.add(label, data=child, expand=False, allow_expand=allow_expand)

            # Recursively add children if it's a directory
            if child.get("children"):
                self._add_children(child_node, child["children"])

    def _update_table(self, files: list) -> None:
        table = self.query_one("#du-table", DataTable)
        table.clear()

        for f in files:
            rel_path = f["path"].relative_to(self.project_dir)
            table.add_row(f["formatted_size"], str(rel_path), key=str(f["path"]))

    @on(Tree.NodeSelected, "#du-tree")
    def on_tree_selected(self, event: Tree.NodeSelected) -> None:
        node_data = event.node.data
        if not node_data:
            return

        self.selected_path = node_data["path"]
        self._update_selection_ui()

    @on(DataTable.RowSelected, "#du-table")
    def on_table_selected(self, event: DataTable.RowSelected) -> None:
        path_str = event.row_key.value
        if path_str:
            self.selected_path = Path(path_str)
            self._update_selection_ui()

    def _update_selection_ui(self) -> None:
        if not self.selected_path:
            return

        lbl = self.query_one("#du-selected-lbl", Label)
        try:
            rel_path = self.selected_path.relative_to(self.project_dir)
        except ValueError:
            rel_path = self.selected_path

        lbl.update(f"Selected: [bold]{rel_path}[/bold]")
        self.query_one("#btn-du-delete").disabled = False

    @on(Button.Pressed, "#btn-du-refresh")
    def on_refresh(self) -> None:
        self.start_scan()

    @on(Button.Pressed, "#btn-du-delete")
    async def on_delete(self) -> None:
        if not self.selected_path:
            return

        path = self.selected_path
        if not path.exists():
            self.notify("File not found.", severity="error")
            return

        if path == self.project_dir:
            self.notify("Cannot delete project root.", severity="error")
            return

        try:
            # Use TrashManager instead of deletion
            trash_id = self.trash_manager.trash(path)
            self.notify(f"Moved to trash: {path.name} ({trash_id})")

            # Refresh
            self.selected_path = None
            self.query_one("#btn-du-delete").disabled = True
            self.query_one("#du-selected-lbl", Label).update("Moved to trash.")
            self.start_scan()

        except Exception as e:
            self.notify(f"Error moving to trash: {e}", severity="error")
