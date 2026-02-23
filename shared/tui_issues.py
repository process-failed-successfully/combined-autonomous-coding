from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Label, DataTable, Button, RichLog, Select
from textual import on
from shared.github_client import GitHubClient
from shared.config_loader import load_config_from_file
import asyncio
import subprocess
import re

class IssuesLabTab(Container):
    """Tab for managing GitHub Issues."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.client = None
        self.selected_issue_number = None
        self.issues_cache = {}

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Issue Tracker[/bold]", classes="welcome-text")

            with Horizontal():
                # Left Pane: Issue List
                with Vertical(id="issue-list-container", classes="stat-box"):
                    with Horizontal():
                        yield Label("[bold]Open Issues[/bold]")
                        yield Select.from_values(["open", "closed", "all"], id="issue-state-select", value="open")

                    yield DataTable(id="issue-table")
                    yield Button("Refresh List", id="btn-issue-refresh", variant="default")

                # Right Pane: Issue Details
                with Vertical(id="issue-details-container"):
                    yield Label("[bold]Issue Details[/bold]")
                    yield RichLog(id="issue-details-log", wrap=True, highlight=True, markup=True)

                    with Horizontal(id="issue-actions", classes="stat-box"):
                        yield Button("Start Work (Branch)", id="btn-issue-start", variant="success", disabled=True)
                        yield Button("View on GitHub", id="btn-issue-web", variant="primary", disabled=True)

    def on_mount(self) -> None:
        self._init_client()
        table = self.query_one("#issue-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Number", "Title", "Assignee", "Labels")

        if self.client:
            self.load_issues()
        else:
            self.query_one("#issue-details-log", RichLog).write("[red]GitHub token not found. Please configure it in agent_config.yaml[/red]")

    def _init_client(self) -> None:
        config = load_config_from_file()
        token = config.get("github_token")
        host = config.get("github_host", "github.com")
        if token:
            self.client = GitHubClient(token=token, host=host)

    def load_issues(self) -> None:
        if not self.client: return

        state = self.query_one("#issue-state-select", Select).value or "open"

        table = self.query_one("#issue-table", DataTable)
        table.clear()
        self.issues_cache = {}

        self.notify(f"Fetching {state} issues...")
        asyncio.create_task(self._fetch_issues(state))

    async def _fetch_issues(self, state: str) -> None:
        try:
            issues = await asyncio.to_thread(self.client.get_issues, self.project_dir, state=state)

            table = self.query_one("#issue-table", DataTable)
            table.clear()

            for issue in issues:
                number = str(issue["number"])
                self.issues_cache[number] = issue

                assignee = "Unassigned"
                if issue.get('assignee'):
                    assignee = issue['assignee']['login']

                labels = ", ".join([l['name'] for l in issue.get('labels', [])])

                table.add_row(
                    number,
                    issue["title"],
                    assignee,
                    labels,
                    key=number
                )

            if not issues:
                self.query_one("#issue-details-log", RichLog).write(f"No {state} issues found.")

        except Exception as e:
            self.notify(f"Error fetching issues: {e}", severity="error")

    @on(DataTable.RowSelected, "#issue-table")
    def on_issue_selected(self, event: DataTable.RowSelected) -> None:
        number = event.row_key.value
        self.selected_issue_number = number
        self._show_details(number)

        # Enable buttons
        self.query_one("#btn-issue-start").disabled = False
        self.query_one("#btn-issue-web").disabled = False

    def _show_details(self, number: str) -> None:
        issue = self.issues_cache.get(number)
        if not issue: return

        log = self.query_one("#issue-details-log", RichLog)
        log.clear()

        log.write(f"[bold]#{issue['number']} {issue['title']}[/bold]")
        log.write(f"State: {issue['state']}")
        log.write(f"Created by: {issue['user']['login']}")
        log.write(f"URL: {issue['html_url']}")
        log.write("\n[bold]Description:[/bold]")
        log.write(issue.get('body', 'No description.'))

    @on(Button.Pressed, "#btn-issue-refresh")
    def on_refresh(self) -> None:
        self.load_issues()

    @on(Select.Changed, "#issue-state-select")
    def on_state_change(self) -> None:
        self.load_issues()

    @on(Button.Pressed, "#btn-issue-web")
    def on_view_web(self) -> None:
        if not self.selected_issue_number: return
        issue = self.issues_cache.get(self.selected_issue_number)
        if issue:
            import webbrowser
            webbrowser.open(issue['html_url'])

    @on(Button.Pressed, "#btn-issue-start")
    async def on_start_work(self) -> None:
        if not self.selected_issue_number: return
        issue = self.issues_cache.get(self.selected_issue_number)
        if not issue: return

        self.notify(f"Starting work on Issue #{issue['number']}...")

        # Branch creation logic (non-blocking)
        try:
            branch_name = await asyncio.to_thread(self._create_branch_logic, issue)
            self.notify(f"Switched to branch: {branch_name}", severity="information")
            self.query_one("#issue-details-log", RichLog).write(f"\n[bold green]Checked out branch: {branch_name}[/bold green]")
        except Exception as e:
            self.notify(f"Error creating branch: {e}", severity="error")

    def _create_branch_logic(self, issue) -> str:
        number = issue['number']
        title = issue['title']

        # Sanitize title
        slug = re.sub(r'[^a-zA-Z0-9]+', '-', title.lower()).strip('-')
        branch_name = f"issue-{number}-{slug}"
        if len(branch_name) > 50:
            branch_name = branch_name[:50].rstrip('-')

        git_path = "git" # Assumed in path

        # Check if branch exists
        try:
            subprocess.run(
                [git_path, "-C", str(self.project_dir), "rev-parse", "--verify", branch_name],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
            )
            # Branch exists, checkout
            subprocess.run(
                [git_path, "-C", str(self.project_dir), "checkout", branch_name],
                check=True, capture_output=True
            )
        except subprocess.CalledProcessError:
            # Branch does not exist, create
            subprocess.run(
                [git_path, "-C", str(self.project_dir), "checkout", "-b", branch_name],
                check=True, capture_output=True
            )

        return branch_name
