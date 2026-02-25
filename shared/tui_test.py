from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Label, Tree, Button, RichLog, Input, Header, Footer
from textual import on
from rich.syntax import Syntax
from shared.test_lab import TestLabManager

class TestLabTab(Container):
    """Tab for interactive Unit Testing."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = TestLabManager(project_dir)
        self.test_data = {}
        self.selected_node_id = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: Test Tree
            with Vertical(id="testlab-tree-container", classes="stat-box"):
                yield Label("[bold]Test Explorer[/bold]")
                with Horizontal():
                    yield Input(placeholder="Filter...", id="testlab-filter")
                    yield Button("Refresh", id="btn-testlab-refresh", variant="default")

                yield Tree("Tests", id="testlab-tree")
                yield Button("Run Selected", id="btn-testlab-run", variant="primary", disabled=True)
                yield Button("Run All", id="btn-testlab-run-all", variant="warning")

            # Right Pane: Output
            with Vertical(id="testlab-output-container"):
                yield Label("[bold]Test Output[/bold]")
                with Horizontal(id="testlab-status-bar", classes="stat-box"):
                    yield Label("Status: Ready", id="lbl-testlab-status")

                yield RichLog(id="testlab-log", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        self.load_tests()

    def load_tests(self) -> None:
        tree = self.query_one("#testlab-tree", Tree)
        tree.clear()
        self.notify("Discovering tests...")

        import asyncio
        asyncio.create_task(self._async_load_tests())

    async def _async_load_tests(self) -> None:
        import asyncio
        data = await asyncio.to_thread(self.manager.collect_tests)

        if "error" in data:
            self.notify(f"Discovery failed: {data['error']}", severity="error")
            return

        self.test_data = data
        tree = self.query_one("#testlab-tree", Tree)
        self._populate_tree(tree.root, data.get("children", []))
        tree.root.expand()
        self.notify("Tests loaded.")

    def _populate_tree(self, tree_node, children_data):
        for child in children_data:
            label = child["name"]
            icon = "📂"
            if child["type"] == "file":
                icon = "📄"
            elif child["type"] == "suite":
                icon = "📦"
            elif child["type"] == "test":
                icon = "🧪"

            display_label = f"{icon} {label}"
            new_node = tree_node.add(display_label, data=child)

            if child.get("children"):
                self._populate_tree(new_node, child["children"])

            # Expand directories by default? Maybe not all.
            if child["type"] == "directory":
                new_node.expand()

    @on(Tree.NodeSelected, "#testlab-tree")
    def on_node_selected(self, event: Tree.NodeSelected) -> None:
        data = event.node.data
        if not data:
            return

        self.selected_node_id = data.get("id") # Might be None for directories

        if self.selected_node_id:
            self.query_one("#btn-testlab-run").disabled = False
            self.query_one("#lbl-testlab-status").update(f"Selected: {data['name']}")
        else:
            self.query_one("#btn-testlab-run").disabled = True
            self.query_one("#lbl-testlab-status").update(f"Selected: {data['name']}")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-testlab-refresh":
            self.load_tests()
        elif event.button.id == "btn-testlab-run":
            await self.run_tests(self.selected_node_id)
        elif event.button.id == "btn-testlab-run-all":
            await self.run_tests(None)

    async def run_tests(self, node_id: str) -> None:
        log = self.query_one("#testlab-log", RichLog)
        status = self.query_one("#lbl-testlab-status", Label)

        log.clear()
        target = node_id if node_id else "ALL TESTS"
        log.write(f"[bold]Running: {target}[/bold]...")
        status.update("Running...")
        self.notify("Tests started...")

        # Disable buttons
        self.query_one("#btn-testlab-run").disabled = True
        self.query_one("#btn-testlab-run-all").disabled = True

        import asyncio

        try:
            result = await asyncio.to_thread(self.manager.run_tests, node_id)

            if result["success"]:
                log.write("[bold green]Tests Passed![/bold green]")
                status.update("[green]Passed[/green]")
            else:
                log.write("[bold red]Tests Failed[/bold red]")
                status.update("[red]Failed[/red]")

            log.write("\n[bold]Output:[/bold]")
            log.write(result["output"])

            if result["error"]:
                log.write("\n[bold red]Stderr:[/bold red]")
                log.write(result["error"])

        except Exception as e:
            log.write(f"[bold red]Error running tests: {e}[/bold red]")
            status.update("Error")
        finally:
            # Re-enable buttons if selection is valid
            if self.selected_node_id:
                self.query_one("#btn-testlab-run").disabled = False
            self.query_one("#btn-testlab-run-all").disabled = False
