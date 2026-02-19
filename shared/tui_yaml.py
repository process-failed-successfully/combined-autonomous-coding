from pathlib import Path
from typing import Any, Optional, List, Union
from textual.app import ComposeResult
from textual.widgets import Label, DirectoryTree, Tree, Input, Button, RichLog
from textual.widgets.tree import TreeNode
from textual.containers import Container, Horizontal, Vertical
from textual import on
from shared.yaml_lab import YamlLabManager
import yaml
import json

class YamlLabTab(Container):
    """
    Interactive YAML Editor Tab.
    """
    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = YamlLabManager()
        self.current_file: Optional[Path] = None
        self.current_data: Any = None
        self.selected_path: Optional[List[Union[str, int]]] = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left: File Browser
            with Vertical(id="yaml-sidebar", classes="stat-box"):
                yield Label("[bold]YAML Files[/bold]")
                yield DirectoryTree(str(self.project_dir), id="yaml-file-tree")

            # Center: YAML Tree
            with Vertical(id="yaml-main", classes="stat-box"):
                yield Label("[bold]Structure[/bold]", id="lbl-yaml-structure")
                yield Tree("Root", id="yaml-tree")

            # Right: Editor
            with Vertical(id="yaml-editor-pane", classes="stat-box"):
                yield Label("[bold]Editor[/bold]")

                yield Label("Path:")
                yield Input(id="yaml-path-input", disabled=True)

                yield Label("Value (YAML/JSON format):")
                yield Input(id="yaml-value-input")

                with Horizontal():
                    yield Button("Update", id="btn-yaml-update", variant="primary", disabled=True)
                    yield Button("Delete", id="btn-yaml-delete", variant="error", disabled=True)

                yield Label("Add Item (to Object/List):")
                yield Input(placeholder="Key (if dict)...", id="yaml-add-key")
                yield Input(placeholder="Value (YAML/JSON)...", id="yaml-add-value")
                yield Button("Add", id="btn-yaml-add", variant="success", disabled=True)

                yield Label("[bold]File Actions[/bold]")
                yield Button("Save File", id="btn-yaml-save", variant="warning", disabled=True)

                yield RichLog(id="yaml-log", wrap=True, highlight=True, markup=True)

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        path = event.path
        if path.suffix.lower() in [".yaml", ".yml"]:
            self.load_file(path)
        else:
            self.notify("Please select a .yaml or .yml file.", severity="warning")

    def load_file(self, path: Path) -> None:
        self.current_file = path
        try:
            # YamlLabManager.load_yaml accepts string or path, but here we read it to be safe or just pass path str
            self.current_data = self.manager.load_yaml(str(path))
            self.build_tree()
            self.query_one("#lbl-yaml-structure", Label).update(f"[bold]Structure: {path.name}[/bold]")
            self.query_one("#btn-yaml-save").disabled = False
            self.log_message(f"Loaded {path.name}")
        except Exception as e:
            self.log_message(f"[red]Error loading YAML: {e}[/red]")
            self.current_data = None
            self.query_one("#yaml-tree", Tree).clear()

    def build_tree(self) -> None:
        tree = self.query_one("#yaml-tree", Tree)
        tree.clear()

        if self.current_data is None:
            return

        root_label = "Object" if isinstance(self.current_data, dict) else "List" if isinstance(self.current_data, list) else "Value"
        tree.root.set_label(root_label)
        tree.root.data = []  # Root path is empty list
        tree.root.expand()

        self._add_nodes(tree.root, self.current_data, [])

    def _add_nodes(self, parent_node: TreeNode, data: Any, current_path: List[Union[str, int]]) -> None:
        if isinstance(data, dict):
            for key, value in data.items():
                path = current_path + [key]
                is_leaf = not isinstance(value, (dict, list))
                label = f"[bold]{key}[/bold]"
                if is_leaf:
                    # Use json.dumps for safe value representation
                    label += f": {json.dumps(value)}"

                node = parent_node.add(label, data=path, expand=False)
                if not is_leaf:
                    self._add_nodes(node, value, path)

        elif isinstance(data, list):
            for i, value in enumerate(data):
                path = current_path + [i]
                is_leaf = not isinstance(value, (dict, list))
                label = f"[{i}]"
                if is_leaf:
                    label += f": {json.dumps(value)}"

                node = parent_node.add(label, data=path, expand=False)
                if not is_leaf:
                    self._add_nodes(node, value, path)

    @on(Tree.NodeSelected, "#yaml-tree")
    def on_node_selected(self, event: Tree.NodeSelected) -> None:
        path = event.node.data
        self.selected_path = path

        # Display path nicely
        display_path = "Root"
        if path:
            display_path = "".join([f"[{k}]" if isinstance(k, int) else f".{k}" for k in path]).lstrip(".")

        self.query_one("#yaml-path-input", Input).value = display_path

        # Get value
        val = self.manager.get(self.current_data, path) if path else self.current_data

        # Update Value Input
        # For editing, we might want to show YAML representation for complex objects, or JSON?
        # JSON is one-line usually, which fits Input better.
        self.query_one("#yaml-value-input", Input).value = json.dumps(val)

        # Enable Buttons
        self.query_one("#btn-yaml-update").disabled = False
        # Cannot delete root (empty list is falsey)
        self.query_one("#btn-yaml-delete").disabled = not bool(path)

        # Enable Add button if container
        is_container = isinstance(val, (dict, list))
        self.query_one("#btn-yaml-add").disabled = not is_container

        if isinstance(val, dict):
            self.query_one("#yaml-add-key").disabled = False
        else:
            self.query_one("#yaml-add-key").disabled = True

    @on(Button.Pressed, "#btn-yaml-update")
    def on_update(self) -> None:
        if self.selected_path is None:
            return

        val_str = self.query_one("#yaml-value-input", Input).value
        try:
            # Use yaml.safe_load to allow YAML syntax in input
            val = yaml.safe_load(val_str)
            self.current_data = self.manager.set(self.current_data, self.selected_path, val)
            self.log_message("Value updated.")
            self.refresh_ui()
        except Exception as e:
            self.log_message(f"[red]Invalid value (must be valid YAML/JSON): {e}[/red]")

    @on(Button.Pressed, "#btn-yaml-delete")
    def on_delete(self) -> None:
        if not self.selected_path:
            return

        try:
            self.current_data = self.manager.delete(self.current_data, self.selected_path)
            self.log_message("Item deleted.")
            self.selected_path = None
            self.refresh_ui()
        except Exception as e:
            self.log_message(f"[red]Delete failed: {e}[/red]")

    @on(Button.Pressed, "#btn-yaml-add")
    def on_add(self) -> None:
        if self.selected_path is None and self.current_data is None:
            return

        path = self.selected_path if self.selected_path is not None else []
        parent = self.manager.get(self.current_data, path) if path else self.current_data

        val_str = self.query_one("#yaml-add-value", Input).value
        try:
            new_val = yaml.safe_load(val_str)
        except Exception:
            self.log_message("[red]Invalid value for add.[/red]")
            return

        try:
            if isinstance(parent, dict):
                key = self.query_one("#yaml-add-key", Input).value
                if not key:
                    self.log_message("[red]Key required for object.[/red]")
                    return
                # Append key to path
                new_path = path + [key]
                self.current_data = self.manager.set(self.current_data, new_path, new_val)

            elif isinstance(parent, list):
                # Append
                idx = len(parent)
                new_path = path + [idx]
                self.current_data = self.manager.set(self.current_data, new_path, new_val)

            self.log_message("Item added.")
            self.refresh_ui()

            # Clear add inputs
            self.query_one("#yaml-add-key", Input).value = ""
            self.query_one("#yaml-add-value", Input).value = ""

        except Exception as e:
            self.log_message(f"[red]Add failed: {e}[/red]")

    @on(Button.Pressed, "#btn-yaml-save")
    def on_save(self) -> None:
        if not self.current_file:
            return

        try:
            with open(self.current_file, 'w', encoding='utf-8') as f:
                f.write(self.manager.dump_yaml(self.current_data))
            self.log_message(f"[green]Saved to {self.current_file.name}[/green]")
        except Exception as e:
            self.log_message(f"[red]Save failed: {e}[/red]")

    def refresh_ui(self) -> None:
        # Rebuild tree
        self.build_tree()
        # Reset editor
        self.query_one("#yaml-path-input", Input).value = ""
        self.query_one("#yaml-value-input", Input).value = ""
        self.query_one("#btn-yaml-update").disabled = True
        self.query_one("#btn-yaml-delete").disabled = True
        self.query_one("#btn-yaml-add").disabled = True

    def log_message(self, message: str) -> None:
        log = self.query_one("#yaml-log", RichLog)
        log.write(message)
