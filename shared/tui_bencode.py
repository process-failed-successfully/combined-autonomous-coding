from pathlib import Path
from typing import Optional, Any
from textual.app import ComposeResult
from textual.widgets import Label, DirectoryTree, Tree, Button, RichLog
from textual.widgets.tree import TreeNode
from textual.containers import Container, Horizontal, Vertical
from textual import on
from shared.bencode_lab import BencodeManager
import json


class BencodeLabTab(Container):
    """
    Interactive Bencode Lab Tab.
    """
    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = BencodeManager()
        self.current_file: Optional[Path] = None
        self.decoded_data: Any = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left: File Browser
            with Vertical(id="bencode-sidebar", classes="stat-box"):
                yield Label("[bold]Torrent / Bencode Files[/bold]")
                yield DirectoryTree(str(self.project_dir), id="bencode-file-tree")

            # Center: Bencode Tree
            with Vertical(id="bencode-main", classes="stat-box"):
                yield Label("[bold]Structure[/bold]", id="lbl-bencode-structure")
                yield Tree("Root", id="bencode-tree")

            # Right: Actions & Output
            with Vertical(id="bencode-actions-pane", classes="stat-box"):
                yield Label("[bold]Actions[/bold]")

                with Horizontal():
                    yield Button("To JSON", id="btn-bencode-json", variant="primary", disabled=True)
                    yield Button("Clear Log", id="btn-bencode-clear-log", variant="default")

                yield Label("[bold]Output / Log[/bold]")
                yield RichLog(id="bencode-log", wrap=True, highlight=True, markup=True)

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        path = event.path
        if path.suffix.lower() in [".torrent", ".bencode"]:
            self.load_file(path)
        else:
            self.notify("Please select a .torrent or .bencode file.", severity="warning")

    def load_file(self, path: Path) -> None:
        self.current_file = path
        try:
            data = path.read_bytes()
            self.decoded_data = self.manager.decode(data)
            self.build_tree()
            self.query_one("#lbl-bencode-structure", Label).update(f"[bold]Structure: {path.name}[/bold]")

            # Enable buttons
            self.query_one("#btn-bencode-json").disabled = False

            self.log_message(f"[green]Loaded {path.name} successfully.[/green]")
        except Exception as e:
            self.log_message(f"[red]Error loading bencode: {e}[/red]")
            self.decoded_data = None
            self.query_one("#bencode-tree", Tree).clear()
            self._disable_buttons()

    def _disable_buttons(self) -> None:
        try:
            self.query_one("#btn-bencode-json", Button).disabled = True
        except Exception:
            pass

    def build_tree(self) -> None:
        tree = self.query_one("#bencode-tree", Tree)
        tree.clear()

        if self.decoded_data is None:
            return

        tree.root.set_label("Root")
        tree.root.data = self.decoded_data
        tree.root.expand()

        # Build nodes from decoded structure
        self._add_nodes(tree.root, self.decoded_data)

    def _add_nodes(self, parent_node: TreeNode[Any], data: Any) -> None:
        if isinstance(data, dict):
            for key, val in data.items():
                label = f"[bold]{key}[/bold]"
                node = parent_node.add(label, expand=False)
                self._add_nodes(node, val)
        elif isinstance(data, list):
            for i, val in enumerate(data):
                label = f"[{i}]"
                node = parent_node.add(label, expand=False)
                self._add_nodes(node, val)
        elif isinstance(data, bytes):
            # Try to decode or hex dump
            try:
                decoded = data.decode('utf-8')
                text = f"[green]\"{decoded[:50]}...\"[/green]" if len(decoded) > 50 else f"[green]\"{decoded}\"[/green]"
            except UnicodeDecodeError:
                hex_str = data.hex()
                text = f"[yellow]0x{hex_str[:20]}...[/yellow]" if len(hex_str) > 20 else f"[yellow]0x{hex_str}[/yellow]"
            parent_node.add_leaf(text)
        elif isinstance(data, int):
            parent_node.add_leaf(f"[blue]{data}[/blue]")
        else:
            parent_node.add_leaf(str(data))

    @on(Button.Pressed, "#btn-bencode-json")
    def on_to_json(self) -> None:
        if self.decoded_data is None:
            return
        try:
            json_safe = self.manager.json_ready(self.decoded_data)
            json_str = json.dumps(json_safe, indent=2)
            self.log_message("[bold]JSON Output:[/bold]")
            self.log_message(json_str)
        except Exception as e:
            self.log_message(f"[red]Conversion Error: {e}[/red]")

    @on(Button.Pressed, "#btn-bencode-clear-log")
    def on_clear_log(self) -> None:
        self.query_one("#bencode-log", RichLog).clear()

    def log_message(self, message: str) -> None:
        log = self.query_one("#bencode-log", RichLog)
        log.write(message)
