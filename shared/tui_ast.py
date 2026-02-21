from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, TextArea, Tree, RichLog
from textual import on
from shared.ast_lab import ASTLabManager
import ast

class ASTExplorerTab(Container):
    """Tab for exploring Python AST."""

    DEFAULT_CSS = """
    ASTExplorerTab {
        layout: vertical;
        height: 100%;
    }

    #ast-main-container {
        height: 70%;
    }

    #code-input-container {
        width: 50%;
        height: 100%;
        border: solid $accent;
    }

    #ast-tree-container {
        width: 50%;
        height: 100%;
        border: solid $secondary;
    }

    #node-details-container {
        height: 30%;
        border: solid $primary;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = ASTLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]AST Explorer[/bold]", classes="welcome-text")

            with Horizontal(id="ast-main-container"):
                # Left: Code Input
                with Vertical(id="code-input-container"):
                    yield Label("Python Code")
                    yield TextArea(language="python", id="code-input")

                # Right: AST Tree
                with Vertical(id="ast-tree-container"):
                    yield Label("AST Structure")
                    yield Tree("Root", id="ast-tree")

            # Bottom: Details
            with Vertical(id="node-details-container"):
                yield Label("Node Details")
                yield RichLog(id="node-details", wrap=True, highlight=True, markup=True)

    @on(TextArea.Changed, "#code-input")
    def on_code_changed(self, event: TextArea.Changed) -> None:
        # Debouncing could be added here, but for now we run on every change (Textual handles some efficiency)
        self.update_tree(event.text_area.text)

    def update_tree(self, code: str) -> None:
        tree = self.query_one("#ast-tree", Tree)
        tree.clear()

        if not code.strip():
            tree.root.label = "Root"
            return

        try:
            root_node = self.manager.parse_code(code)
            tree.root.label = "Module"
            tree.root.data = root_node

            self._build_tree(tree.root, root_node)
            tree.root.expand()
        except ValueError as e:
            tree.root.label = f"[red]Syntax Error: {e}[/red]"

    def _build_tree(self, tree_node, ast_node):
        """Recursively adds nodes to the tree."""
        # ast_node can be a list or an AST node
        if isinstance(ast_node, list):
            for item in ast_node:
                self._build_tree(tree_node, item)
            return

        if not isinstance(ast_node, ast.AST):
            return

        # Iterate over fields to find child nodes
        for field, value in ast.iter_fields(ast_node):
            if isinstance(value, list):
                if not value: continue
                # Create a group node for list fields (e.g. body)
                # group_node = tree_node.add(f"[bold]{field}[/bold]", expand=True)
                # Actually, standard AST viewers usually show list items directly or under the field name
                # Let's show list items under the field name

                # Check if list contains AST nodes
                if all(isinstance(v, (ast.AST, type(None))) for v in value):
                     field_node = tree_node.add(f"[dim]{field}[/dim]", expand=True)
                     for item in value:
                         if item:
                             self._add_single_node(field_node, item)

            elif isinstance(value, ast.AST):
                self._add_single_node(tree_node, value, prefix=f"{field}=")

    def _add_single_node(self, parent, node, prefix=""):
        name = node.__class__.__name__
        label = f"{prefix}[blue]{name}[/blue]"

        # Add some quick info to label if possible (e.g. Name id)
        if isinstance(node, ast.Name):
            label += f" [green]'{node.id}'[/green]"
        elif isinstance(node, ast.Constant):
            label += f" [yellow]{node.value!r}[/yellow]"
        elif isinstance(node, ast.FunctionDef):
            label += f" [bold]{node.name}[/bold]"
        elif isinstance(node, ast.ClassDef):
            label += f" [bold]{node.name}[/bold]"

        new_node = parent.add(label, data=node, expand=False)
        self._build_tree(new_node, node)

    @on(Tree.NodeSelected, "#ast-tree")
    def on_node_selected(self, event: Tree.NodeSelected) -> None:
        node = event.node.data
        details_log = self.query_one("#node-details", RichLog)
        details_log.clear()

        if not node or not isinstance(node, ast.AST):
            return

        # Highlight code
        if hasattr(node, "lineno") and hasattr(node, "end_lineno"):
            editor = self.query_one("#code-input", TextArea)
            # Textual TextArea uses 0-based indexing for selection?
            # select(start, end)
            # We can just scroll to it for now as selection programmatic API might vary by version
            # Or just print info
            details_log.write(f"[bold]Location:[/bold] Line {node.lineno} - {node.end_lineno}")

        # Dump info
        info = self.manager.node_to_dict(node)

        # Pretty print fields
        details_log.write(f"[bold purple]{node.__class__.__name__}[/bold purple]")

        for k, v in info.get("attributes", {}).items():
             details_log.write(f"  [cyan]{k}:[/cyan] {v}")

        for k, v in info.get("fields", {}).items():
            if isinstance(v, dict) and "type" in v: # It's a node
                 details_log.write(f"  [yellow]{k}:[/yellow] <{v['type']}>")
            elif isinstance(v, list):
                 details_log.write(f"  [yellow]{k}:[/yellow] List[{len(v)}]")
            else:
                 details_log.write(f"  [yellow]{k}:[/yellow] {v!r}")
