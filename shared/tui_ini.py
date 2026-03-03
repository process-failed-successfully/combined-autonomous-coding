from pathlib import Path
from typing import Optional
from textual.app import ComposeResult
from textual.widgets import Label, DirectoryTree, Tree, Input, Button, RichLog, TabbedContent, TabPane
from textual.containers import Container, Horizontal, Vertical
from textual import on
from shared.ini_lab import IniLabManager


class IniLabTab(Container):
    """Interactive INI Editor Tab."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = IniLabManager()
        self.current_file: Optional[Path] = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left panel: DirectoryTree
            with Vertical(id="ini-left-panel", classes="sidebar"):
                yield Label("Select an INI file (.ini, .cfg):", classes="panel-title")
                yield DirectoryTree(self.project_dir, id="ini-dir-tree")

            # Right panel: Viewer/Editor
            with Vertical(id="ini-right-panel", classes="main-content"):
                yield Label("INI Viewer", id="ini-status", classes="panel-title")
                with TabbedContent(id="ini-tabs"):
                    with TabPane("View", id="ini-tab-view"):
                        yield Tree("INI Data", id="ini-data-tree")

                    with TabPane("Edit Key", id="ini-tab-edit"):
                        yield Label("Select a section/key in the Tree to edit.")
                        yield Input(placeholder="Section", id="ini-edit-section")
                        yield Input(placeholder="Key", id="ini-edit-key")
                        yield Input(placeholder="Value", id="ini-edit-value")
                        with Horizontal(classes="buttons-row"):
                            yield Button("Set", variant="primary", id="ini-btn-set")
                            yield Button("Delete Key", variant="error", id="ini-btn-del-key")
                            yield Button("Delete Section", variant="error", id="ini-btn-del-sec")

                yield RichLog(id="ini-log", highlight=True, markup=True)

    def on_mount(self) -> None:
        tree = self.query_one("#ini-dir-tree", DirectoryTree)
        tree.guide_depth = 3

    @on(DirectoryTree.FileSelected, "#ini-dir-tree")
    def on_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        path = Path(event.path)
        if path.suffix.lower() in [".ini", ".cfg", ".conf"]:
            self.current_file = path
            self.query_one("#ini-status", Label).update(f"Editing: {path.name}")
            self.refresh_data()
        else:
            self._log_msg(f"[yellow]Ignored {path.name} (not .ini/.cfg/.conf)[/yellow]")

    def refresh_data(self) -> None:
        if not self.current_file:
            return

        try:
            config = self.manager._read_config(self.current_file)
            tree = self.query_one("#ini-data-tree", Tree)
            tree.clear()
            tree.root.label = self.current_file.name

            for section in config.sections():
                sec_node = tree.root.add(f"[bold blue][{section}][/bold blue]", data={"type": "section", "section": section})
                for key, value in config.items(section):
                    sec_node.add(f"[green]{key}[/green] = [yellow]{value}[/yellow]", data={"type": "key", "section": section, "key": key, "value": value})

            tree.root.expand_all()
            self._log_msg(f"[green]Loaded {self.current_file.name}[/green]")
        except Exception as e:
            self._log_msg(f"[red]Error loading file: {e}[/red]")

    @on(Tree.NodeSelected, "#ini-data-tree")
    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        if not event.node.data:
            return

        node_data = event.node.data
        section_input = self.query_one("#ini-edit-section", Input)
        key_input = self.query_one("#ini-edit-key", Input)
        value_input = self.query_one("#ini-edit-value", Input)

        if node_data["type"] == "section":
            section_input.value = str(node_data.get("section", ""))
            key_input.value = ""
            value_input.value = ""
        elif node_data["type"] == "key":
            section_input.value = str(node_data.get("section", ""))
            key_input.value = str(node_data.get("key", ""))
            value_input.value = str(node_data.get("value", ""))

        self.query_one("#ini-tabs", TabbedContent).active = "ini-tab-edit"

    @on(Button.Pressed, "#ini-btn-set")
    def handle_set(self) -> None:
        if not self.current_file:
            self._log_msg("[red]No file selected.[/red]")
            return

        sec = self.query_one("#ini-edit-section", Input).value.strip()
        k = self.query_one("#ini-edit-key", Input).value.strip()
        v = self.query_one("#ini-edit-value", Input).value.strip()

        if not sec or not k:
            self._log_msg("[red]Section and Key are required.[/red]")
            return

        try:
            self.manager.set(str(self.current_file), sec, k, v)
            self._log_msg(f"[green]Set {sec}.{k} = {v}[/green]")
            self.refresh_data()
        except Exception as e:
            self._log_msg(f"[red]Error setting key: {e}[/red]")

    @on(Button.Pressed, "#ini-btn-del-key")
    def handle_del_key(self) -> None:
        if not self.current_file:
            self._log_msg("[red]No file selected.[/red]")
            return

        sec = self.query_one("#ini-edit-section", Input).value.strip()
        k = self.query_one("#ini-edit-key", Input).value.strip()

        if not sec or not k:
            self._log_msg("[red]Section and Key are required for deletion.[/red]")
            return

        try:
            self.manager.delete(str(self.current_file), sec, k)
            self._log_msg(f"[green]Deleted {sec}.{k}[/green]")
            self.refresh_data()
        except Exception as e:
            self._log_msg(f"[red]Error deleting key: {e}[/red]")

    @on(Button.Pressed, "#ini-btn-del-sec")
    def handle_del_sec(self) -> None:
        if not self.current_file:
            self._log_msg("[red]No file selected.[/red]")
            return

        sec = self.query_one("#ini-edit-section", Input).value.strip()

        if not sec:
            self._log_msg("[red]Section is required for deletion.[/red]")
            return

        try:
            self.manager.delete(str(self.current_file), sec)
            self._log_msg(f"[green]Deleted section {sec}[/green]")
            self.refresh_data()
        except Exception as e:
            self._log_msg(f"[red]Error deleting section: {e}[/red]")

    def _log_msg(self, msg: str) -> None:
        try:
            log = self.query_one("#ini-log", RichLog)
            log.write(msg)
        except Exception:
            pass
