from pathlib import Path
from typing import Optional
from textual.app import ComposeResult
from textual.widgets import Label, DirectoryTree, Tree, Input, Button, RichLog, DataTable
from textual.widgets.tree import TreeNode
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual import on
from shared.html_lab import HTMLLabManager, HTMLNode

class HtmlLabTab(Container):
    """
    Interactive HTML Inspector Tab.
    """
    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = HTMLLabManager()
        self.current_file: Optional[Path] = None
        self.root_node: Optional[HTMLNode] = None
        self.filter_text: str = ""

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left: File Browser
            with Vertical(id="html-sidebar", classes="stat-box"):
                yield Label("[bold]HTML Files[/bold]")
                yield DirectoryTree(str(self.project_dir), id="html-file-tree")

            # Center: DOM Tree
            with Vertical(id="html-main", classes="stat-box"):
                yield Label("[bold]DOM Tree[/bold]", id="lbl-html-structure")
                yield Input(placeholder="Filter tags/id/class...", id="html-tree-filter")
                yield Tree("Root", id="html-tree")

            # Right: Details
            with Vertical(id="html-details-pane", classes="stat-box"):
                yield Label("[bold]Attributes[/bold]")
                yield DataTable(id="html-attr-table")

                yield Label("[bold]Text Content[/bold]")
                yield RichLog(id="html-text-log", wrap=True, highlight=False)

    def on_mount(self) -> None:
        table = self.query_one("#html-attr-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Attribute", "Value")

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        path = event.path
        if path.suffix.lower() in [".html", ".htm", ".xml", ".svg"]:
            self.load_file(path)
        else:
            self.notify("Please select an HTML file.", severity="warning")

    def load_file(self, path: Path) -> None:
        self.current_file = path
        try:
            content = path.read_text(encoding="utf-8")
            self.root_node = self.manager.tree(content)
            self.build_tree()
            self.query_one("#lbl-html-structure", Label).update(f"[bold]DOM: {path.name}[/bold]")
            self.notify(f"Loaded {path.name}")
        except Exception as e:
            self.notify(f"Error loading HTML: {e}", severity="error")
            self.query_one("#html-tree", Tree).clear()

    @on(Input.Changed, "#html-tree-filter")
    def on_filter_changed(self, event: Input.Changed) -> None:
        self.filter_text = event.value
        self.build_tree()

    def build_tree(self) -> None:
        tree = self.query_one("#html-tree", Tree)
        tree.clear()

        if self.root_node is None:
            return

        tree.root.set_label("Document")
        tree.root.data = self.root_node
        tree.root.expand()

        # The root node in HTMLNode ("root") contains the top-level elements (html, doctype, etc)
        # We iterate over its children
        for child in self.root_node.children:
            self._add_nodes(tree.root, child)

    def _add_nodes(self, parent_node: TreeNode, html_node: HTMLNode) -> None:
        # Prepare label
        tag = html_node.tag
        node_id = html_node.attrs.get("id")
        classes = html_node.attrs.get("class")

        label = f"[bold blue]{tag}[/bold blue]"
        if node_id:
            label += f"[yellow]#{node_id}[/yellow]"
        if classes:
            label += f"[green].{classes.replace(' ', '.')}[/green]"

        # Filter logic
        # Simple string match on tag, id, class
        search_target = f"{tag} {node_id or ''} {classes or ''}".lower()
        match = not self.filter_text or self.filter_text.lower() in search_target

        # If match, add it. If children match, add it and expand.
        # This is a simple recursive approach: add if self matches OR any child matches (but displaying entire subtree if parent matches might be too much, usually we filter strictly or show path to match)

        # Strategy: Add node if it matches OR if it has matching descendants.
        # If filter is empty, add everything.

        if self.filter_text:
            if match:
                # Add this node and all children (expand=True)
                t_node = parent_node.add(label, data=html_node, expand=True)
                for child in html_node.children:
                    self._add_nodes_recursive(t_node, child) # Add all children recursively
            else:
                # Check if any descendant matches
                if self._has_matching_descendant(html_node):
                    # Add this node (expanded) to show path to child
                    t_node = parent_node.add(label, data=html_node, expand=True)
                    for child in html_node.children:
                        self._add_nodes(t_node, child)
        else:
            # No filter
            t_node = parent_node.add(label, data=html_node)
            for child in html_node.children:
                self._add_nodes(t_node, child)

    def _add_nodes_recursive(self, parent_node: TreeNode, html_node: HTMLNode):
        """Adds nodes unconditionally."""
        tag = html_node.tag
        node_id = html_node.attrs.get("id")
        classes = html_node.attrs.get("class")
        label = f"[bold blue]{tag}[/bold blue]"
        if node_id: label += f"[yellow]#{node_id}[/yellow]"
        if classes: label += f"[green].{classes.replace(' ', '.')}[/green]"

        t_node = parent_node.add(label, data=html_node)
        for child in html_node.children:
            self._add_nodes_recursive(t_node, child)

    def _has_matching_descendant(self, html_node: HTMLNode) -> bool:
        tag = html_node.tag
        node_id = html_node.attrs.get("id")
        classes = html_node.attrs.get("class")
        search_target = f"{tag} {node_id or ''} {classes or ''}".lower()

        if self.filter_text.lower() in search_target:
            return True

        for child in html_node.children:
            if self._has_matching_descendant(child):
                return True
        return False

    @on(Tree.NodeSelected, "#html-tree")
    def on_node_selected(self, event: Tree.NodeSelected) -> None:
        node_data: HTMLNode = event.node.data
        if not node_data:
            return

        # Update Attributes Table
        table = self.query_one("#html-attr-table", DataTable)
        table.clear()

        if node_data.attrs:
            for k, v in node_data.attrs.items():
                table.add_row(k, v)
        else:
            table.add_row("No attributes", "")

        # Update Text Content
        log = self.query_one("#html-text-log", RichLog)
        log.clear()
        if node_data.text:
            log.write(node_data.text)
        else:
            log.write("[italic]No text content[/italic]")
