import asyncio
import shutil
from pathlib import Path
from typing import Any

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, Button, Tree, DataTable, Static
from textual import on
from textual.binding import Binding

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
                    yield Button("Delete Permanently", id="btn-du-perm-delete", variant="error", disabled=True)

    def on_mount(self) -> None:
        table = self.query_one("#du-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Size", "File Path")

        self.start_scan()

    def start_scan(self) -> None:
        tree = self.query_one("#du-tree", Tree)
        tree.clear()
        tree.root.label = "Scanning..."
        # Disable buttons during scan
        self.query_one("#btn-du-refresh").disabled = True
        self.notify("Scanning disk usage...")
        asyncio.create_task(self._scan_task())

    async def _scan_task(self) -> None:
        # Run scan in thread
        self.scan_data = await asyncio.to_thread(scan_disk_usage, self.project_dir)
        largest_files = await asyncio.to_thread(get_largest_files, self.project_dir)

        # Update UI
        self._update_tree(self.scan_data)
        self._update_table(largest_files)
        self.query_one("#btn-du-refresh").disabled = False
        self.notify("Scan complete.")

    def _update_tree(self, data: dict) -> None:
        tree = self.query_one("#du-tree", Tree)
        tree.clear()

        if not data:
            tree.root.label = "Scan failed or empty."
            return

        root_size = format_size(data.get("size", 0))
        root_label = f"{self.project_dir.name} ({root_size})"
        tree.root.label = root_label
        tree.root.data = data

        # We expand the root by default
        tree.root.expand()

        # Add immediate children of root
        self._add_tree_children(tree.root, data.get("children", []))

    def _add_tree_children(self, node: Any, children: list) -> None:
        """Adds immediate children to the tree node."""
        for child in children:
            size_str = format_size(child["size"])
            label = f"{child['name']} ({size_str})"
            is_dir = child["type"] == "dir"

            # If it's a directory, we allow expand, but don't add children yet (lazy load)
            # UNLESS it's empty, in which case expand is useless?
            # If children list is empty, allow_expand=False?
            # scan_disk_usage populates "children" list.
            has_children = bool(child.get("children"))
            allow_expand = is_dir and has_children

            node.add(label, data=child, expand=False, allow_expand=allow_expand)

    @on(Tree.NodeExpanded, "#du-tree")
    def on_tree_node_expanded(self, event: Tree.NodeExpanded) -> None:
        node = event.node
        # If node already has children in the UI, don't add them again
        if node.children:
            return

        node_data = node.data
        if not node_data:
            return

        children_data = node_data.get("children", [])
        if children_data:
            self._add_tree_children(node, children_data)

    def _update_table(self, files: list) -> None:
        table = self.query_one("#du-table", DataTable)
        table.clear()

        for f in files:
            try:
                rel_path = f["path"].relative_to(self.project_dir)
            except ValueError:
                rel_path = f["path"]
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

        is_root = self.selected_path == self.project_dir
        self.query_one("#btn-du-delete").disabled = is_root
        self.query_one("#btn-du-perm-delete").disabled = is_root

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
            self._on_action_complete()
        except Exception as e:
            self.notify(f"Error moving to trash: {e}", severity="error")

    @on(Button.Pressed, "#btn-du-perm-delete")
    async def on_perm_delete(self) -> None:
        if not self.selected_path:
            return

        path = self.selected_path
        if not path.exists():
            self.notify("File not found.", severity="error")
            return

        if path == self.project_dir:
            self.notify("Cannot delete project root.", severity="error")
            return

        # Simple confirmation by notification? Or assume user knows what they are doing since it's "red" button?
        # Ideally we'd pop a modal, but for now we'll just do it.
        # Wait, let's verify if path is safe? (not root, already checked)

        try:
            if path.is_file() or path.is_symlink():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path)

            self.notify(f"Permanently deleted: {path.name}")
            self._on_action_complete()
        except Exception as e:
            self.notify(f"Error deleting: {e}", severity="error")

    def _on_action_complete(self) -> None:
        """Reset selection and refresh scan."""
        self.selected_path = None
        self.query_one("#btn-du-delete").disabled = True
        self.query_one("#btn-du-perm-delete").disabled = True
        self.query_one("#du-selected-lbl", Label).update("Action complete.")
        self.start_scan()
