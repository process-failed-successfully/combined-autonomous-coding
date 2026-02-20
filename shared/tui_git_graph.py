import asyncio
from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Label, Button, RichLog
from textual import on
from rich.text import Text
from shared.git import get_git_graph_lines

class GitGraphPane(Container):
    """Pane for visualizing Git Graph."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        with Vertical(classes="stat-box"):
            with Horizontal():
                yield Label("[bold]Git Graph[/bold]", classes="header-label")
                yield Button("Refresh", id="btn-refresh-graph", variant="primary")

            # wrap=False ensures graph lines align correctly
            yield RichLog(id="git-graph-view", wrap=False, highlight=False, markup=False)

    def on_mount(self) -> None:
        self.load_graph()

    def load_graph(self) -> None:
        log_view = self.query_one("#git-graph-view", RichLog)
        log_view.clear()
        log_view.write("Loading graph...")

        # Run in background to avoid freezing UI
        asyncio.create_task(self._async_load_graph())

    async def _async_load_graph(self) -> None:
        try:
            lines = await asyncio.to_thread(get_git_graph_lines, self.project_dir)
            log_view = self.query_one("#git-graph-view", RichLog)
            log_view.clear()

            for line in lines:
                # Convert ANSI codes from git output to Rich Text
                log_view.write(Text.from_ansi(line))

        except Exception as e:
            self.notify(f"Error loading graph: {e}", severity="error")

    @on(Button.Pressed, "#btn-refresh-graph")
    def on_refresh(self) -> None:
        self.load_graph()
        self.notify("Graph refreshed.")
