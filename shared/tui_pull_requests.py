from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Label, DataTable, Button, RichLog, Markdown
from textual import on
from shared.github_client import GitHubClient
from shared.config_loader import load_config_from_file
import asyncio

class PullRequestsTab(Container):
    """Tab for managing GitHub Pull Requests."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.client = None
        self.selected_pr_number = None
        self.pr_cache = {}

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Pull Request Manager[/bold]", classes="welcome-text")

            with Horizontal():
                # Left Pane: PR List
                with Vertical(id="pr-list-container", classes="stat-box"):
                    yield Label("[bold]Open Pull Requests[/bold]")
                    yield DataTable(id="pr-table")
                    yield Button("Refresh List", id="btn-pr-refresh", variant="default")

                # Right Pane: PR Details
                with Vertical(id="pr-details-container"):
                    yield Label("[bold]PR Details[/bold]")
                    yield RichLog(id="pr-details-log", wrap=True, highlight=True, markup=True)

                    with Horizontal(id="pr-actions", classes="stat-box"):
                        yield Button("View Checks", id="btn-pr-checks", variant="primary", disabled=True)
                        yield Button("Merge", id="btn-pr-merge", variant="success", disabled=True)
                        yield Button("Close", id="btn-pr-close", variant="error", disabled=True)

    def on_mount(self) -> None:
        self._init_client()
        table = self.query_one("#pr-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Number", "Title", "Author", "Created")

        if self.client:
            self.load_prs()
        else:
            self.query_one("#pr-details-log", RichLog).write("[red]GitHub token not found. Please configure it in agent_config.yaml[/red]")

    def _init_client(self) -> None:
        config = load_config_from_file()
        token = config.get("github_token")
        host = config.get("github_host", "github.com")
        if token:
            self.client = GitHubClient(token=token, host=host)

    def load_prs(self) -> None:
        if not self.client: return

        table = self.query_one("#pr-table", DataTable)
        table.clear()
        self.pr_cache = {}

        asyncio.create_task(self._fetch_prs())

    async def _fetch_prs(self) -> None:
        try:
            prs = await asyncio.to_thread(self.client.list_pull_requests, self.project_dir)

            table = self.query_one("#pr-table", DataTable)
            table.clear()

            for pr in prs:
                number = str(pr["number"])
                self.pr_cache[number] = pr
                table.add_row(
                    number,
                    pr["title"],
                    pr["user"]["login"],
                    pr["created_at"][:10],
                    key=number
                )

            if not prs:
                self.query_one("#pr-details-log", RichLog).write("No open PRs found.")

        except Exception as e:
            self.notify(f"Error fetching PRs: {e}", severity="error")

    @on(DataTable.RowSelected, "#pr-table")
    def on_pr_selected(self, event: DataTable.RowSelected) -> None:
        number = event.row_key.value
        self.selected_pr_number = number
        self._show_details(number)

        # Enable buttons
        self.query_one("#btn-pr-checks").disabled = False
        self.query_one("#btn-pr-merge").disabled = False
        self.query_one("#btn-pr-close").disabled = False

    def _show_details(self, number: str) -> None:
        pr = self.pr_cache.get(number)
        if not pr: return

        log = self.query_one("#pr-details-log", RichLog)
        log.clear()

        log.write(f"[bold]#{pr['number']} {pr['title']}[/bold]")
        log.write(f"Author: {pr['user']['login']}")
        log.write(f"URL: {pr['html_url']}")
        log.write(f"State: {pr['state']}")
        log.write("\n[bold]Description:[/bold]")
        log.write(pr.get('body', 'No description.'))

    @on(Button.Pressed, "#btn-pr-refresh")
    def on_refresh(self) -> None:
        self.load_prs()
        self.notify("Refreshing PRs...")

    @on(Button.Pressed, "#btn-pr-checks")
    async def on_checks(self) -> None:
        if not self.selected_pr_number: return
        pr = self.pr_cache.get(self.selected_pr_number)
        head_sha = pr['head']['sha']

        log = self.query_one("#pr-details-log", RichLog)
        log.write("\n[bold]Fetching Checks...[/bold]")

        try:
            checks = await asyncio.to_thread(self.client.get_pull_request_checks, self.project_dir, head_sha)

            if not checks.get("check_runs"):
                log.write("No check runs found.")
            else:
                for check in checks["check_runs"]:
                    status = check["status"]
                    conclusion = check["conclusion"] or "pending"
                    color = "green" if conclusion == "success" else "red" if conclusion == "failure" else "yellow"
                    log.write(f"- {check['name']}: [{color}]{status}/{conclusion}[/{color}]")

        except Exception as e:
            log.write(f"[red]Error fetching checks: {e}[/red]")

    @on(Button.Pressed, "#btn-pr-merge")
    async def on_merge(self) -> None:
        if not self.selected_pr_number: return
        self.notify(f"Merging PR #{self.selected_pr_number}...")

        try:
            res = await asyncio.to_thread(self.client.merge_pull_request, self.project_dir, int(self.selected_pr_number))
            if res.get("merged"):
                self.notify("PR merged successfully!", severity="information")
                self.load_prs()
                self.query_one("#pr-details-log", RichLog).write("\n[bold green]Merged![/bold green]")
            else:
                self.notify(f"Merge failed: {res.get('message')}", severity="error")
        except Exception as e:
            self.notify(f"Error merging: {e}", severity="error")

    @on(Button.Pressed, "#btn-pr-close")
    async def on_close(self) -> None:
        if not self.selected_pr_number: return
        self.notify(f"Closing PR #{self.selected_pr_number}...")

        try:
            res = await asyncio.to_thread(self.client.close_pull_request, self.project_dir, int(self.selected_pr_number))
            if res.get("state") == "closed":
                self.notify("PR closed successfully.", severity="information")
                self.load_prs()
                self.query_one("#pr-details-log", RichLog).write("\n[bold red]Closed![/bold red]")
        except Exception as e:
            self.notify(f"Error closing: {e}", severity="error")
