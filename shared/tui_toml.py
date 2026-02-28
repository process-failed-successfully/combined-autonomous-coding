from pathlib import Path
from typing import Any, Optional, List, Union
from textual.app import ComposeResult
from textual.widgets import Label, DirectoryTree, Tree, Input, Button, RichLog
from textual.widgets.tree import TreeNode
from textual.containers import Container, Horizontal, Vertical
from textual import on
from shared.toml_lab import TomlLabManager
import json

class TomlLabTab(Container):
    """
    Interactive TOML Editor Tab.
    """
    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = TomlLabManager()
        self.current_file: Optional[Path] = None
        self.current_data: Any = None
        self.selected_path: Optional[List[Union[str, int]]] = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left: File Browser
            with Vertical(id="toml-sidebar", classes="stat-box"):
                yield Label("[bold]TOML Files[/bold]")
                yield DirectoryTree(str(self.project_dir), id="toml-file-tree")

            # Center: TOML Tree
            with Vertical(id="toml-main", classes="stat-box"):
                yield Label("[bold]Structure[/bold]", id="lbl-toml-structure")
                yield Tree("Root", id="toml-tree")

            # Right: Editor
            with Vertical(id="toml-editor-pane", classes="stat-box"):
                yield Label("[bold]Editor[/bold]")

                yield Label("Path:")
                yield Input(id="toml-path-input", disabled=True)

                yield Label("Value (JSON format):")
                yield Input(id="toml-value-input")

                with Horizontal():
                    yield Button("Update", id="btn-toml-update", variant="primary", disabled=True)
                    yield Button("Delete", id="btn-toml-delete", variant="error", disabled=True)

                yield Label("Add Item (to Object/List):")
                yield Input(placeholder="Key (if dict)...", id="toml-add-key")
                yield Input(placeholder="Value (JSON)...", id="toml-add-value")
                yield Button("Add", id="btn-toml-add", variant="success", disabled=True)

                yield Label("[bold]File Actions[/bold]")
                yield Button("Save File", id="btn-toml-save", variant="warning", disabled=True)

                yield RichLog(id="toml-log", wrap=True, highlight=True, markup=True)

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        path = event.path
        if path.suffix.lower() == ".toml":
            self.load_file(path)
        else:
            self.notify("Please select a .toml file.", severity="warning")

    def load_file(self, path: Path) -> None:
        self.current_file = path
        try:
            self.current_data = self.manager.load_toml(str(path))
            self.build_tree()
            self.query_one("#lbl-toml-structure", Label).update(f"[bold]Structure: {path.name}[/bold]")
            self.query_one("#btn-toml-save").disabled = False
            self.log_message(f"Loaded {path.name}")
        except Exception as e:
            self.log_message(f"[red]Error loading TOML: {e}[/red]")
            self.current_data = None
            self.query_one("#toml-tree", Tree).clear()

    def build_tree(self) -> None:
        tree = self.query_one("#toml-tree", Tree)
        tree.clear()

        if self.current_data is None:
            return

        root_label = "Object" if hasattr(self.current_data, "get") or isinstance(self.current_data, dict) else "List" if isinstance(self.current_data, list) else "Value"
        tree.root.set_label(root_label)
        tree.root.data = []  # Root path is empty list
        tree.root.expand()

        self._add_nodes(tree.root, self.current_data, [])

    def _add_nodes(self, parent_node: TreeNode, data: Any, current_path: List[Union[str, int]]) -> None:
        if hasattr(data, "items") or isinstance(data, dict):
            for key, value in data.items():
                path = current_path + [key]
                is_leaf = not (hasattr(value, "get") or isinstance(value, (dict, list)))
                label = f"[bold]{key}[/bold]"
                if is_leaf:
                    # Unwrap tomlkit objects for display if needed
                    val_to_dump = value.unwrap() if hasattr(value, "unwrap") else value
                    label += f": {json.dumps(val_to_dump)}"

                node = parent_node.add(label, data=path, expand=False)
                if not is_leaf:
                    self._add_nodes(node, value, path)

        elif isinstance(data, list):
            for i, value in enumerate(data):
                path = current_path + [i]
                is_leaf = not (hasattr(value, "get") or isinstance(value, (dict, list)))
                label = f"[{i}]"
                if is_leaf:
                    val_to_dump = value.unwrap() if hasattr(value, "unwrap") else value
                    label += f": {json.dumps(val_to_dump)}"

                node = parent_node.add(label, data=path, expand=False)
                if not is_leaf:
                    self._add_nodes(node, value, path)

    @on(Tree.NodeSelected, "#toml-tree")
    def on_node_selected(self, event: Tree.NodeSelected) -> None:
        path = event.node.data
        self.selected_path = path

        # Display path nicely
        display_path = "Root"
        if path:
            display_path = "".join([f"[{k}]" if isinstance(k, int) else f".{k}" for k in path]).lstrip(".")

        self.query_one("#toml-path-input", Input).value = display_path

        # Get value
        val = self.manager.get(self.current_data, path) if path else self.current_data

        # Unwrap for JSON editing
        val_to_dump = val.unwrap() if hasattr(val, "unwrap") else val

        # Update Value Input
        self.query_one("#toml-value-input", Input).value = json.dumps(val_to_dump)

        # Enable Buttons
        self.query_one("#btn-toml-update").disabled = False
        # Cannot delete root (empty list is falsey)
        self.query_one("#btn-toml-delete").disabled = not bool(path)

        # Enable Add button if container
        is_container = hasattr(val, "get") or isinstance(val, (dict, list))
        self.query_one("#btn-toml-add").disabled = not is_container

        if hasattr(val, "get") or isinstance(val, dict):
            self.query_one("#toml-add-key").disabled = False
        else:
            self.query_one("#toml-add-key").disabled = True

    @on(Button.Pressed, "#btn-toml-update")
    def on_update(self) -> None:
        if self.selected_path is None:
            return

        val_str = self.query_one("#toml-value-input", Input).value
        try:
            val = json.loads(val_str)
            self.current_data = self.manager.set(self.current_data, self.selected_path, val)
            self.log_message("Value updated.")
            self.refresh_ui()
        except json.JSONDecodeError:
            self.log_message("[red]Invalid JSON value.[/red]")
        except Exception as e:
            self.log_message(f"[red]Update failed: {e}[/red]")

    @on(Button.Pressed, "#btn-toml-delete")
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

    @on(Button.Pressed, "#btn-toml-add")
    def on_add(self) -> None:
        if self.selected_path is None and self.current_data is None:
            return

        path = self.selected_path if self.selected_path is not None else []
        parent = self.manager.get(self.current_data, path) if path else self.current_data

        val_str = self.query_one("#toml-add-value", Input).value
        try:
            new_val = json.loads(val_str)
        except Exception:
            self.log_message("[red]Invalid JSON value for add.[/red]")
            return

        try:
            if hasattr(parent, "get") or isinstance(parent, dict):
                key = self.query_one("#toml-add-key", Input).value
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
            self.query_one("#toml-add-key", Input).value = ""
            self.query_one("#toml-add-value", Input).value = ""

        except Exception as e:
            self.log_message(f"[red]Add failed: {e}[/red]")

    @on(Button.Pressed, "#btn-toml-save")
    def on_save(self) -> None:
        if not self.current_file:
            return

        try:
            with open(self.current_file, 'w', encoding='utf-8') as f:
                f.write(self.manager.dump_toml(self.current_data))
            self.log_message(f"[green]Saved to {self.current_file.name}[/green]")
        except Exception as e:
            self.log_message(f"[red]Save failed: {e}[/red]")

    def refresh_ui(self) -> None:
        # Rebuild tree
        self.build_tree()
        # Reset editor
        self.query_one("#toml-path-input", Input).value = ""
        self.query_one("#toml-value-input", Input).value = ""
        self.query_one("#btn-toml-update").disabled = True
        self.query_one("#btn-toml-delete").disabled = True
        self.query_one("#btn-toml-add").disabled = True

    def log_message(self, message: str) -> None:
        log = self.query_one("#toml-log", RichLog)
        log.write(message)
