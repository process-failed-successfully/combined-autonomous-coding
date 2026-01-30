import asyncio
from typing import List, Dict, cast
from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Label, Button, Input, DataTable, Select, Markdown

from shared.standup import get_commits_since, generate_standup_report


class StandupTab(Container):
    """Tab for generating daily standup reports."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.commits_cache: List[Dict[str, str]] = []

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Standup Generator[/bold]", classes="welcome-text")

            # Controls
            with Horizontal(classes="stat-box"):
                yield Label("Since:")
                yield Input(value="24 hours ago", placeholder="e.g. 24 hours ago", id="standup-since")
                yield Label("Author:")
                yield Input(placeholder="Name (optional)", id="standup-author")
                yield Button("Fetch Commits", id="btn-standup-fetch", variant="primary")

            with Horizontal(id="standup-content"):
                # Left Pane: Commits Table
                with Vertical(id="standup-left-pane", classes="stat-box"):
                    yield Label("[bold]Activity[/bold]")
                    yield DataTable(id="standup-table")
                    yield Label("", id="standup-status")

                # Right Pane: Report
                with Vertical(id="standup-right-pane", classes="stat-box"):
                    yield Label("[bold]Report[/bold]")
                    with Horizontal():
                        yield Select.from_values(["gemini", "cursor", "local"], id="standup-agent", value="gemini")
                        yield Button("Generate Report (AI)", id="btn-standup-generate", variant="success", disabled=True)

                    with VerticalScroll():
                        yield Markdown("Fetch commits to start...", id="standup-markdown")

    def on_mount(self) -> None:
        table = self.query_one("#standup-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Time", "Hash", "Subject")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-standup-fetch":
            await self.fetch_commits()
        elif event.button.id == "btn-standup-generate":
            await self.generate_report()

    async def fetch_commits(self) -> None:
        since = self.query_one("#standup-since", Input).value
        author = self.query_one("#standup-author", Input).value

        self.query_one("#standup-status", Label).update("Fetching commits...")
        self.notify("Fetching commits...")

        # Run in thread
        commits = await asyncio.to_thread(
            get_commits_since,
            self.project_dir,
            since,
            author if author else None
        )

        self.commits_cache = commits
        self._update_table(commits)

        if commits:
            self.query_one("#standup-status", Label).update(f"Found {len(commits)} commits.")
            self.query_one("#btn-standup-generate").disabled = False
            self.query_one("#standup-markdown", Markdown).update("Ready to generate.")
        else:
            self.query_one("#standup-status", Label).update("No commits found.")
            self.query_one("#btn-standup-generate").disabled = True
            self.query_one("#standup-markdown", Markdown).update("No commits found.")

    def _update_table(self, commits: List[Dict[str, str]]) -> None:
        table = self.query_one("#standup-table", DataTable)
        table.clear()
        for c in commits:
            table.add_row(c["date"], c["hash"][:7], c["subject"])

    async def generate_report(self) -> None:
        if not self.commits_cache:
            return

        agent_type = cast(str, self.query_one("#standup-agent", Select).value or "gemini")
        since = self.query_one("#standup-since", Input).value

        self.notify(f"Generating report with {agent_type}...", severity="information")
        md_view = self.query_one("#standup-markdown", Markdown)
        md_view.update("Thinking... please wait.")

        report = await generate_standup_report(
            commits=self.commits_cache,
            agent_type=agent_type,
            project_dir=self.project_dir,
            since=since
        )

        md_view.update(report)
        self.notify("Report generated.")
