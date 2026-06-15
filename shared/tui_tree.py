from textual.app import ComposeResult
from textual.widgets import Label, Button, Input, RichLog
from textual.containers import Container, Horizontal, Vertical
from textual import on
from pathlib import Path
from shared.tree_lab import TreeLabManager
import asyncio

class TreeLabTab(Container):
    """Tab for generating ASCII directory trees."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Tree Lab[/bold]", classes="welcome-text")

            with Vertical(classes="stat-box"):
                yield Label("Directory Path (default: .):")
                yield Input(placeholder="e.g. . or /path/to/dir", id="input-tree-dir")

                yield Label("Max Depth (-1 for infinite):")
                yield Input(value="-1", id="input-tree-depth")

                yield Label("Excludes (comma-separated):")
                yield Input(placeholder="e.g. .git,node_modules,__pycache__", id="input-tree-excludes")

                with Horizontal():
                    yield Button("Generate Tree", id="btn-tree-generate", variant="primary")

                yield Label("[bold]Tree Output[/bold]")
                yield RichLog(id="log-tree-output", wrap=False, highlight=True, markup=False)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-tree-generate":
            await self.generate_tree()

    async def generate_tree(self) -> None:
        dir_val = self.query_one("#input-tree-dir", Input).value.strip() or "."
        depth_val = self.query_one("#input-tree-depth", Input).value.strip()
        excludes_val = self.query_one("#input-tree-excludes", Input).value.strip()
        log = self.query_one("#log-tree-output", RichLog)

        # Parse Depth
        try:
            max_depth = int(depth_val)
        except ValueError:
            self.notify("Max depth must be an integer.", severity="error")
            return

        # Parse excludes
        if excludes_val:
            excludes = [ex.strip() for ex in excludes_val.split(",") if ex.strip()]
        else:
            excludes = None

        manager = TreeLabManager(exclude=excludes)
        target_dir = Path(dir_val)

        log.clear()

        if not target_dir.exists():
            log.write(f"Error: Directory '{target_dir}' does not exist.")
            self.notify("Directory does not exist.", severity="error")
            return

        try:
            # CPU bound operation, but string concatenation tree traversal
            tree_str = await asyncio.to_thread(manager.generate_tree, target_dir, max_depth)

            output = f"{target_dir.resolve().name}/\n{tree_str}"
            log.write(output)
            self.notify("Tree generated successfully.")
        except Exception as e:
            log.write(f"Error generating tree: {e}")
            self.notify(f"Error generating tree: {e}", severity="error")
