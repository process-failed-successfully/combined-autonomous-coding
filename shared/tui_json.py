from pathlib import Path
from typing import Any, Optional, List, Union
from textual.app import ComposeResult
from textual.widgets import Label, DirectoryTree, Tree, Input, Button, RichLog, TabbedContent, TabPane, DataTable
from textual.widgets.tree import TreeNode
from textual.containers import Container, Horizontal, Vertical
from textual import on
from shared.json_lab import JsonLabManager
import json


class JsonLabTab(Container):
    """
    Interactive JSON Editor Tab.
    """
    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = JsonLabManager()
        self.current_file: Optional[Path] = None
        self.current_data: Any = None
        self.selected_path: Optional[List[Union[str, int]]] = None
        self.filter_text: str = ""

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left: File Browser
            with Vertical(id="json-sidebar", classes="stat-box"):
                yield Label("[bold]JSON Files[/bold]")
                yield DirectoryTree(str(self.project_dir), id="json-file-tree")

            # Center: JSON Tree
            with Vertical(id="json-main", classes="stat-box"):
                yield Label("[bold]Structure[/bold]", id="lbl-json-structure")
                yield Input(placeholder="Filter nodes...", id="json-tree-filter")
                yield Tree("Root", id="json-tree")

            # Right: Editor & Query
            with Vertical(id="json-editor-pane", classes="stat-box"):
                with TabbedContent(id="json-mode-tabs"):
                    with TabPane("Edit", id="tab-json-edit"):
                        yield Label("[bold]Editor[/bold]")

                        yield Label("Path:")
                        yield Input(id="json-path-input", disabled=True)

                        yield Label("Value (JSON format):")
                        yield Input(id="json-value-input")

                        with Horizontal():
                            yield Button("Update", id="btn-json-update", variant="primary", disabled=True)
                            yield Button("Delete", id="btn-json-delete", variant="error", disabled=True)

                        yield Label("Add Item (to Object/List):")
                        yield Input(placeholder="Key (if dict)...", id="json-add-key")
                        yield Input(placeholder="Value (JSON)...", id="json-add-value")
                        yield Button("Add", id="btn-json-add", variant="success", disabled=True)

                        yield Label("[bold]File Actions[/bold]")
                        yield Button("Save File", id="btn-json-save", variant="warning", disabled=True)

                    with TabPane("Query", id="tab-json-query"):
                        yield Label("[bold]Advanced Query[/bold]")
                        yield Label("Python Expression (use 'data'):")
                        yield Input(placeholder="[x for x in data['items'] if x['id'] > 10]", id="json-query-input")
                        yield Button("Run Query", id="btn-json-run-query", variant="success")

                        yield Label("[bold]Result[/bold]")
                        with TabbedContent():
                            with TabPane("Table"):
                                yield DataTable(id="json-query-table")
                            with TabPane("JSON"):
                                yield RichLog(id="json-query-log", wrap=True, highlight=True, markup=True)

                yield RichLog(id="json-log", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        table = self.query_one("#json-query-table", DataTable)
        table.cursor_type = "row"

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        path = event.path
        if path.suffix.lower() == ".json":
            self.load_file(path)
        else:
            self.notify("Please select a .json file.", severity="warning")

    def load_file(self, path: Path) -> None:
        self.current_file = path
        try:
            self.current_data = self.manager.load_json(str(path))
            self.build_tree()
            self.query_one("#lbl-json-structure", Label).update(f"[bold]Structure: {path.name}[/bold]")
            self.query_one("#btn-json-save").disabled = False
            self.log_message(f"Loaded {path.name}")
        except Exception as e:
            self.log_message(f"[red]Error loading JSON: {e}[/red]")
            self.current_data = None
            self.query_one("#json-tree", Tree).clear()

    @on(Input.Changed, "#json-tree-filter")
    def on_filter_changed(self, event: Input.Changed) -> None:
        self.filter_text = event.value
        self.build_tree()

    def build_tree(self) -> None:
        tree = self.query_one("#json-tree", Tree)
        tree.clear()

        if self.current_data is None:
            return

        root_label = "Object" if isinstance(self.current_data, dict) else "List" if isinstance(self.current_data, list) else "Value"
        tree.root.set_label(root_label)
        tree.root.data = []  # Root path is empty list
        tree.root.expand()

        self._add_nodes(tree.root, self.current_data, [])

    def _add_nodes(self, parent_node: TreeNode, data: Any, current_path: List[Union[str, int]]) -> None:
        def matches_filter(text: str) -> bool:
            if not self.filter_text:
                return True
            return self.filter_text.lower() in text.lower()

        if isinstance(data, dict):
            for key, value in data.items():
                path = current_path + [key]
                is_leaf = not isinstance(value, (dict, list))

                label = f"[bold]{key}[/bold]"
                plain_text = str(key)

                if is_leaf:
                    val_str = json.dumps(value)
                    label += f": {val_str}"
                    plain_text += f": {val_str}"

                # Filter Logic:
                # 1. If leaf node: show only if matches filter.
                # 2. If container node: always show (to allow traversing to matching children),
                #    unless we implement deep search which is expensive.
                if is_leaf and not matches_filter(plain_text):
                    continue

                # Expand containers if filtering is active to reveal matches deeper down
                expanded = bool(self.filter_text)

                node = parent_node.add(label, data=path, expand=expanded)
                if not is_leaf:
                    self._add_nodes(node, value, path)

        elif isinstance(data, list):
            for i, value in enumerate(data):
                path = current_path + [i]
                is_leaf = not isinstance(value, (dict, list))

                label = f"[{i}]"
                plain_text = f"[{i}]"

                if is_leaf:
                    val_str = json.dumps(value)
                    label += f": {val_str}"
                    plain_text += f": {val_str}"

                if is_leaf and not matches_filter(plain_text):
                    continue

                expanded = bool(self.filter_text)
                node = parent_node.add(label, data=path, expand=expanded)
                if not is_leaf:
                    self._add_nodes(node, value, path)

    @on(Tree.NodeSelected, "#json-tree")
    def on_node_selected(self, event: Tree.NodeSelected) -> None:
        path = event.node.data
        self.selected_path = path

        # Display path nicely
        display_path = "Root"
        if path:
            display_path = "".join([f"[{k}]" if isinstance(k, int) else f".{k}" for k in path]).lstrip(".")

        self.query_one("#json-path-input", Input).value = display_path

        # Get value
        val = self.manager.get(self.current_data, path) if path else self.current_data

        # Update Value Input
        self.query_one("#json-value-input", Input).value = json.dumps(val)

        # Enable Buttons
        self.query_one("#btn-json-update").disabled = False
        # Cannot delete root (empty list is falsey)
        self.query_one("#btn-json-delete").disabled = not bool(path)

        # Enable Add button if container
        is_container = isinstance(val, (dict, list))
        self.query_one("#btn-json-add").disabled = not is_container

        if isinstance(val, dict):
            self.query_one("#json-add-key").disabled = False
        else:
            self.query_one("#json-add-key").disabled = True  # List doesn't need key

    @on(Button.Pressed, "#btn-json-update")
    def on_update(self) -> None:
        if self.selected_path is None:
            return

        val_str = self.query_one("#json-value-input", Input).value
        try:
            val = json.loads(val_str)
            self.current_data = self.manager.set(self.current_data, self.selected_path, val)
            self.log_message("Value updated.")
            self.refresh_ui()
        except json.JSONDecodeError:
            self.log_message("[red]Invalid JSON value.[/red]")
        except Exception as e:
            self.log_message(f"[red]Update failed: {e}[/red]")

    @on(Button.Pressed, "#btn-json-delete")
    def on_delete(self) -> None:
        if not self.selected_path:
            return

        try:
            self.current_data = self.manager.delete(self.current_data, self.selected_path)
            self.log_message("Item deleted.")
            self.selected_path = None  # Reset selection
            self.refresh_ui()
        except Exception as e:
            self.log_message(f"[red]Delete failed: {e}[/red]")

    @on(Button.Pressed, "#btn-json-add")
    def on_add(self) -> None:
        # Check explicit None for selected_path, but handle empty list (root) correctly
        if self.selected_path is None and self.current_data is None:
            return

        path = self.selected_path if self.selected_path is not None else []
        parent = self.manager.get(self.current_data, path) if path else self.current_data

        val_str = self.query_one("#json-add-value", Input).value
        try:
            new_val = json.loads(val_str)
        except Exception:
            self.log_message("[red]Invalid JSON value for add.[/red]")
            return

        try:
            if isinstance(parent, dict):
                key = self.query_one("#json-add-key", Input).value
                if not key:
                    self.log_message("[red]Key required for object.[/red]")
                    return
                # Append key to path
                new_path = path + [key]
                self.current_data = self.manager.set(self.current_data, new_path, new_val)

            elif isinstance(parent, list):
                # JsonLabManager set appends if index == len
                idx = len(parent)
                new_path = path + [idx]
                self.current_data = self.manager.set(self.current_data, new_path, new_val)

            self.log_message("Item added.")
            self.refresh_ui()

            # Clear add inputs
            self.query_one("#json-add-key", Input).value = ""
            self.query_one("#json-add-value", Input).value = ""

        except Exception as e:
            self.log_message(f"[red]Add failed: {e}[/red]")

    @on(Button.Pressed, "#btn-json-save")
    def on_save(self) -> None:
        if not self.current_file:
            return

        try:
            with open(self.current_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_data, f, indent=2)
            self.log_message(f"[green]Saved to {self.current_file.name}[/green]")
        except Exception as e:
            self.log_message(f"[red]Save failed: {e}[/red]")

    @on(Button.Pressed, "#btn-json-run-query")
    def on_run_query(self) -> None:
        if self.current_data is None:
            self.notify("No JSON loaded.", severity="warning")
            return

        expr = self.query_one("#json-query-input", Input).value
        if not expr:
            self.notify("Query expression required.", severity="error")
            return

        log = self.query_one("#json-query-log", RichLog)
        log.clear()

        table = self.query_one("#json-query-table", DataTable)
        table.clear(columns=True)

        try:
            result = self.manager.query(self.current_data, expr)

            # Check if result is list of dicts -> populate table
            if isinstance(result, list) and result and isinstance(result[0], dict):
                keys = list(result[0].keys())
                table.add_columns(*keys)
                for item in result:
                    # Handle missing keys or different structure partially
                    row = [str(item.get(k, "")) for k in keys]
                    table.add_row(*row)
                log.write(f"Displaying {len(result)} rows in Table.")
            else:
                log.write(json.dumps(result, indent=2, default=str))

        except Exception as e:
            log.write(f"[bold red]Query Error:[/bold red] {e}")

    def refresh_ui(self) -> None:
        # Rebuild tree
        self.build_tree()
        # Reset editor
        self.query_one("#json-path-input", Input).value = ""
        self.query_one("#json-value-input", Input).value = ""
        self.query_one("#btn-json-update").disabled = True
        self.query_one("#btn-json-delete").disabled = True
        self.query_one("#btn-json-add").disabled = True

    def log_message(self, message: str) -> None:
        log = self.query_one("#json-log", RichLog)
        log.write(message)
