import sys
import io
import contextlib
import os
import shlex
import asyncio
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, RichLog, DirectoryTree, TabbedContent, TabPane, Button, Label, Input, DataTable, Select, Markdown
from textual.containers import Container, Horizontal, VerticalScroll, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.binding import Binding
from textual.coordinate import Coordinate
from textual import on

from shared.cli_utils import get_latest_log_file, get_workflow_stage
from shared.knowledge import KnowledgeManager
from shared.ask import run_ask_logic
from shared.optimize import OptimizationManager
from shared.dependencies import DependencyAnalyzer, DependencyUpdater
from shared.database import init_db
from shared.github_client import GitHubClient
from shared.config_loader import load_config_from_file

# Helper to get Git info safely
def get_git_info(project_dir: Path) -> dict:
    import shutil
    import subprocess
    git_path = shutil.which("git")
    info = {"branch": "Unknown", "status": "Unknown"}
    if git_path and (project_dir / ".git").is_dir():
        try:
            # Get branch
            res = subprocess.run([git_path, "-C", str(project_dir), "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True)
            if res.returncode == 0:
                info["branch"] = res.stdout.strip()

            # Get status (clean/dirty)
            res = subprocess.run([git_path, "-C", str(project_dir), "status", "--porcelain"], capture_output=True, text=True)
            if res.returncode == 0:
                info["status"] = "Dirty" if res.stdout.strip() else "Clean"
        except Exception:
            pass
    return info

class DashboardTab(Container):
    """The main dashboard tab."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Label("Welcome to Mission Control", classes="welcome-text")

            # Project Info
            with Container(classes="stat-box"):
                yield Label(f"[bold]Project:[/bold] {self.project_dir.name}")
                yield Label(f"[bold]Path:[/bold] {self.project_dir}")

            # Git Status
            git_info = get_git_info(self.project_dir)
            with Container(classes="stat-box"):
                yield Label(f"[bold]Git Branch:[/bold] {git_info['branch']}")
                yield Label(f"[bold]Git Status:[/bold] {git_info['status']}")

            # Workflow Stage
            stage = get_workflow_stage(self.project_dir)
            with Container(classes="stat-box"):
                yield Label(f"[bold]Workflow Stage:[/bold] {stage}")

            # Recent History
            with Container(classes="stat-box"):
                yield Label("[bold]Recent Agent Runs[/bold]")
                yield RichLog(id="history-log")

            # Quick Actions
            with Container(classes="stat-box"):
                yield Label("[bold]Quick Actions[/bold]")
                with Horizontal():
                    yield Button("Run Tests", id="btn-test", variant="primary")
                    yield Button("Run Lint", id="btn-lint", variant="warning")
                    yield Button("Refresh", id="btn-refresh", variant="success")

    def on_mount(self) -> None:
        self.update_history()

    def update_history(self) -> None:
        history_log = self.query_one("#history-log", RichLog)
        history_log.clear()
        history_file = self.project_dir / ".agent_history"
        if history_file.exists():
            try:
                with open(history_file, "r") as f:
                    # Get last 5 lines
                    lines = f.readlines()
                    for line in reversed(lines[-5:]):
                        history_log.write(line.strip())
            except Exception:
                history_log.write("Error reading history.")
        else:
            history_log.write("No history found.")

class FileExplorerTab(Container):
    """Tab for browsing files."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical(id="left-pane"):
                yield DirectoryTree(str(self.project_dir), id="file-tree")
            with Vertical(id="right-pane"):
                yield RichLog(id="file-preview", wrap=True, highlight=True, markup=True)

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        preview = self.query_one("#file-preview", RichLog)
        preview.clear()
        preview.write(f"[bold]{event.path}[/bold]\n")
        try:
            # Limit file size for preview
            if event.path.stat().st_size > 100 * 1024:
                preview.write("File too large to preview.")
                return

            with open(event.path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
                preview.write(content)
        except Exception as e:
            preview.write(f"Error reading file: {e}")

class LogsTab(Container):
    """Tab for viewing logs."""

    def compose(self) -> ComposeResult:
        yield RichLog(id="log-viewer", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        self.update_log()
        self.set_interval(2, self.update_log)

    def update_log(self) -> None:
        log_viewer = self.query_one("#log-viewer", RichLog)
        log_file = get_latest_log_file()

        if log_file and log_file.exists():
            try:
                # Basic tail implementation
                with open(log_file, "r", encoding="utf-8", errors="replace") as f:
                    # Read last 200 lines to avoid performance issues
                    lines = f.readlines()
                    log_viewer.clear()
                    log_viewer.write("".join(lines[-200:]))
            except Exception as e:
                log_viewer.clear()
                log_viewer.write(f"Error reading log: {e}")
        else:
            log_viewer.clear()
            log_viewer.write("No log file found.")

class InteractTab(Container):
    """Tab for interacting with the agent (Chat)."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        with Vertical():
            yield RichLog(id="chat-history", wrap=True, highlight=True, markup=True)
            with Horizontal(id="chat-controls", classes="stat-box"):
                yield Select.from_values(["gemini", "cursor", "local"], id="agent-select", value="gemini")
                yield Input(placeholder="Ask a question or give an instruction...", id="chat-input")

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        query = event.value
        if not query:
            return

        chat_log = self.query_one("#chat-history", RichLog)
        chat_log.write(f"[bold blue]You:[/bold blue] {query}")

        # Clear input
        event.input.value = ""

        # Get selected agent
        agent_select = self.query_one("#agent-select", Select)
        agent_type = agent_select.value or "gemini"

        chat_log.write(f"[italic]Agent ({agent_type}) is thinking...[/italic]")

        # Run logic capturing stdout
        output_capture = io.StringIO()
        success = False
        with contextlib.redirect_stdout(output_capture):
            try:
                # We use run_ask_logic for now as it's safer than 'do' which executes code
                success = await run_ask_logic(
                    query=query,
                    project_dir=self.project_dir,
                    agent_type=agent_type,
                    verbose=False
                )
            except Exception as e:
                print(f"Error: {e}")

        response = output_capture.getvalue()

        # Format response
        if success:
             chat_log.write(f"[bold green]Agent:[/bold green]")
             chat_log.write(response)
        else:
             chat_log.write(f"[bold red]Agent Error:[/bold red]")
             chat_log.write(response)

class KnowledgeTab(Container):
    """Tab for managing knowledge."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = KnowledgeManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Knowledge Base[/bold]", classes="welcome-text")
            yield DataTable(id="knowledge-table")
            with Horizontal(classes="stat-box"):
                yield Input(placeholder="Add new knowledge...", id="knowledge-input")
                yield Button("Add", id="btn-add-knowledge", variant="primary")
            yield Button("Refresh", id="btn-refresh-knowledge", variant="default")

    def on_mount(self) -> None:
        # Init DB
        init_db(self.project_dir / ".agent_db.sqlite")

        table = self.query_one("#knowledge-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("ID", "Category", "Content", "Source")
        self.load_knowledge()

    def load_knowledge(self) -> None:
        table = self.query_one("#knowledge-table", DataTable)
        table.clear()
        try:
            items = self.manager.list_knowledge()
            for item in items:
                table.add_row(str(item.id), item.category, item.content, item.source_agent)
        except Exception as e:
            self.notify(f"Error loading knowledge: {e}", severity="error")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-refresh-knowledge":
            self.load_knowledge()
            self.notify("Knowledge refreshed.")
        elif event.button.id == "btn-add-knowledge":
            inp = self.query_one("#knowledge-input", Input)
            content = inp.value
            if content:
                try:
                    self.manager.add_knowledge(content, source="user_tui")
                    self.notify("Knowledge added.")
                    inp.value = ""
                    self.load_knowledge()
                except Exception as e:
                    self.notify(f"Error adding knowledge: {e}", severity="error")
            else:
                self.notify("Content cannot be empty.", severity="warning")

class IssuesTab(Container):
    """Tab for viewing GitHub Issues."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.issues_cache = []

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]GitHub Issues[/bold]", classes="welcome-text")
            with Horizontal(classes="stat-box"):
                yield Button("Refresh", id="btn-issues-refresh", variant="primary")
                yield Select.from_values(["open", "closed"], id="select-issue-state", value="open")
                yield Input(placeholder="Filter by title...", id="input-issue-filter")

            yield DataTable(id="issues-table")

    def on_mount(self) -> None:
        table = self.query_one("#issues-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Number", "Title", "Assignee", "Labels")
        # Ensure we don't double load if Select triggers on_changed immediately
        # But Textual 0.73 might behave differently.
        # Let's rely on on_mount for initial load.
        self.load_issues()

    def load_issues(self) -> None:
        table = self.query_one("#issues-table", DataTable)
        table.clear()

        # Load config to get token
        file_config = load_config_from_file()
        github_token = file_config.get("github_token") or os.environ.get("GITHUB_TOKEN")
        github_host = file_config.get("github_host", "github.com")

        if not github_token:
            self.notify("GitHub token not found. Please run 'configure'.", severity="error")
            return

        state_select = self.query_one("#select-issue-state", Select)
        state = state_select.value or "open"

        client = GitHubClient(token=github_token, host=github_host)

        try:
            issues = client.get_issues(self.project_dir, state=state)
            self.issues_cache = issues
            self._update_table(issues)
            self.notify(f"Loaded {len(issues)} issues.")
        except Exception as e:
            self.notify(f"Error fetching issues: {e}", severity="error")

    def _update_table(self, issues: list) -> None:
        table = self.query_one("#issues-table", DataTable)
        table.clear()

        filter_text = self.query_one("#input-issue-filter", Input).value.lower()

        for issue in issues:
            title = issue['title']
            if filter_text and filter_text not in title.lower():
                continue

            number = str(issue['number'])

            assignee = "Unassigned"
            if issue.get('assignee'):
                assignee = issue['assignee']['login']

            labels = ", ".join([l['name'] for l in issue.get('labels', [])])

            table.add_row(number, title, assignee, labels)

    @on(Button.Pressed, "#btn-issues-refresh")
    def refresh_issues(self):
        self.load_issues()

    @on(Select.Changed, "#select-issue-state")
    def filter_state(self):
        self.load_issues()

    @on(Input.Changed, "#input-issue-filter")
    def filter_issues(self):
        self._update_table(self.issues_cache)

class DependenciesTab(Container):
    """Tab for managing project dependencies."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.analyzer = DependencyAnalyzer(project_dir)
        self.updater = DependencyUpdater(project_dir)
        self.current_data = {}
        # Keep track of row keys -> dependency info for updating
        self.row_map = {}

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Dependencies[/bold]", classes="welcome-text")

            with Horizontal(classes="stat-box"):
                yield Button("Scan", id="btn-deps-scan", variant="primary")
                yield Button("Check Updates", id="btn-deps-check", variant="warning")
                yield Button("Update Selected", id="btn-deps-update", variant="error", disabled=True)

            yield DataTable(id="deps-table")

    def on_mount(self) -> None:
        table = self.query_one("#deps-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Language", "Package", "Current", "Latest", "Type", "Status")
        self.scan_dependencies()

    async def scan_dependencies(self) -> None:
        self.notify("Scanning dependencies...")
        # Run scan in a thread to avoid blocking
        self.current_data = await asyncio.to_thread(self.analyzer.scan)
        self._refresh_table()
        self.notify("Scan complete.")

    async def check_updates(self) -> None:
        self.notify("Checking for updates (this may take a moment)...", severity="information", timeout=5)
        # Run check_updates in a thread
        # Pass verbose=False to avoid stdout noise
        self.current_data = await asyncio.to_thread(self.analyzer.check_updates, self.current_data, verbose=False)
        self._refresh_table()
        self.notify("Update check complete.")

    def _refresh_table(self) -> None:
        table = self.query_one("#deps-table", DataTable)
        table.clear()
        self.row_map = {}

        # Flatten the data structure
        # data = { "python": [ { "source": "...", "dependencies": [...] } ], ... }

        for lang, files in self.current_data.items():
            for file_info in files:
                source_file = file_info["source"]
                # Store full path for updater
                full_path = self.project_dir / source_file

                for dep in file_info.get("dependencies", []):
                    name = dep["name"]
                    current = dep.get("version", "")
                    latest = dep.get("latest", "")
                    dtype = dep.get("type", "prod")
                    is_outdated = dep.get("outdated", False)

                    status = "[red]Outdated[/red]" if is_outdated else "[green]OK[/green]"
                    if not latest:
                        status = "Unknown"

                    row_key = table.add_row(
                        lang.capitalize(),
                        name,
                        current,
                        latest or "-",
                        dtype,
                        status
                    )

                    # Store info needed for update
                    self.row_map[row_key] = {
                        "file_path": full_path,
                        "name": name,
                        "latest": latest,
                        "type": dtype,
                        "outdated": is_outdated
                    }

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        # Enable update button if the selected row is outdated and has a latest version
        row_key = event.row_key
        info = self.row_map.get(row_key)

        btn = self.query_one("#btn-deps-update", Button)
        if info and info["outdated"] and info["latest"]:
            btn.disabled = False
            btn.label = f"Update {info['name']} to {info['latest']}"
        else:
            btn.disabled = True
            btn.label = "Update Selected"

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-deps-scan":
            await self.scan_dependencies()
        elif event.button.id == "btn-deps-check":
            await self.check_updates()
        elif event.button.id == "btn-deps-update":
            await self.update_selected()

    async def update_selected(self) -> None:
        table = self.query_one("#deps-table", DataTable)
        cursor_row = table.cursor_row
        if cursor_row is None:
            return

        # Get row key from index
        # Textual's DataTable doesn't easily expose key from cursor index directly in all versions,
        # but coordinate (row_index, col_index) works.
        # We need the RowKey to look up in self.row_map.
        # table.coordinate_to_cell_key(Coordinate(cursor_row, 0)).row_key
        # Coordinate is imported at top level
        try:
             # This might depend on textual version.
             # Safe way: iterate rows and match index?
             # Or check if `table.get_row_at(cursor_row)` returns keys? No.
             # Actually `on_data_table_row_selected` gives us the key, so we can cache it.
             # But the user might move the cursor without selecting?
             # Textual: "Selection" usually means clicking or pressing Enter.
             # "Cursor" is just highlighting.
             # Let's rely on the last selected row via on_data_table_row_selected if possible.
             # But the button press is a separate event.
             pass
        except:
             pass

        # Since we enabling the button based on selection, we assume selection is active.
        # But `table.cursor_row` might be different from selection if multiple selection is off?
        # Let's verify selection.
        # `table.selection` returns a set of RowKeys.
        # We only support single update for now.

        # NOTE: DataTable selection logic can be tricky.
        # Let's assume the user MUST select a row (click/enter) which triggers `on_data_table_row_selected`
        # and enables the button. We just need to know WHICH row was selected.
        # We can store `self.selected_row_key` in `on_data_table_row_selected`.

        # However, I didn't add `self.selected_row_key` to `__init__`.
        # Let's rely on `table.cursor_row` and mapping it to key if possible,
        # OR simply iterating `table.rows` (which is a dict of key->row).
        # Actually `table.get_row_at(index)` returns the data list.
        # `table.coordinate_to_cell_key` is robust.

        key = table.coordinate_to_cell_key(Coordinate(cursor_row, 0)).row_key
        info = self.row_map.get(key)

        if not info:
            self.notify("No valid dependency selected.", severity="error")
            return

        if not info["outdated"] or not info["latest"]:
            self.notify("Selected dependency is not outdated or latest version is unknown.", severity="warning")
            return

        self.notify(f"Updating {info['name']} to {info['latest']}...")

        success = await asyncio.to_thread(
            self.updater.update_dependency,
            info["file_path"],
            info["name"],
            info["latest"],
            info["type"]
        )

        if success:
            self.notify(f"Successfully updated {info['name']}.")
            # Refresh to reflect changes
            await self.scan_dependencies()
            # We might want to re-check updates too, but scan is a good start.
            # Ideally we update the local state to avoid full re-scan/check loop,
            # but that's complex.
        else:
            self.notify(f"Failed to update {info['name']}.", severity="error")

class ProfileTab(Container):
    """Tab for performance profiling."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = OptimizationManager(project_dir)
        self.stats_file = None

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Performance Profiler[/bold]", classes="welcome-text")

            with Horizontal(classes="stat-box"):
                yield Label("Script:", classes="label")
                yield Input(placeholder="path/to/script.py", id="profile-script-input")
                yield Label("Args:", classes="label")
                yield Input(placeholder="--arg val", id="profile-args-input")
                yield Button("Run Profile", id="btn-run-profile", variant="primary")

            yield DataTable(id="profile-table")

            with Horizontal(classes="stat-box"):
                yield Button("Analyze with AI", id="btn-analyze-profile", variant="warning", disabled=True)
                yield Select.from_values(["gemini", "cursor", "local"], id="profile-agent-select", value="gemini")

            with VerticalScroll(id="profile-output-container"):
                yield Markdown(id="profile-ai-output")

    def on_mount(self) -> None:
        table = self.query_one("#profile-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Function", "File:Line", "Calls", "Total Time", "Cum Time")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-run-profile":
            await self.run_profiler()
        elif event.button.id == "btn-analyze-profile":
            await self.analyze_profile()

    async def run_profiler(self):
        script_val = self.query_one("#profile-script-input", Input).value
        args_val = self.query_one("#profile-args-input", Input).value

        if not script_val:
            self.notify("Please enter a script path.", severity="error")
            return

        script_path = self.project_dir / script_val
        if not script_path.exists():
            self.notify(f"Script not found: {script_val}", severity="error")
            return

        args = shlex.split(args_val) if args_val else []

        self.notify("Running profiler...", severity="information")
        self.stats_file = self.manager.run_profile(script_path, args)

        if self.stats_file:
            self.notify("Profiling complete.")
            self.load_stats()
            self.query_one("#btn-analyze-profile").disabled = False
        else:
            self.notify("Profiling failed.", severity="error")

    def load_stats(self):
        table = self.query_one("#profile-table", DataTable)
        table.clear()
        if not self.stats_file:
            return

        stats = self.manager.analyze_stats(self.stats_file, limit=20)

        for func in stats:
            location = f"{Path(func['filename']).name}:{func['line']}"
            table.add_row(
                func['name'],
                location,
                str(func['ncalls']),
                f"{func['tottime']:.4f}s",
                f"{func['cumtime']:.4f}s"
            )

    async def analyze_profile(self):
        if not self.stats_file:
            return

        agent_select = self.query_one("#profile-agent-select", Select)
        agent_type = agent_select.value or "gemini"

        self.notify(f"Asking {agent_type} for optimization tips...")
        ai_output = self.query_one("#profile-ai-output", Markdown)
        ai_output.update("Thinking...")

        suggestion = await self.manager.get_ai_suggestions(self.stats_file, agent_type=agent_type)
        ai_output.update(suggestion)
        self.notify("Analysis complete.")

class AgentTUI(App):
    """Mission Control TUI."""

    CSS_PATH = "tui.css"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "toggle_dark", "Toggle Dark Mode"),
    ]

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent():
            with TabPane("Dashboard", id="tab-dashboard"):
                yield DashboardTab(self.project_dir)
            with TabPane("Interact", id="tab-interact"):
                yield InteractTab(self.project_dir)
            with TabPane("Dependencies", id="tab-deps"):
                yield DependenciesTab(self.project_dir)
            with TabPane("Issues", id="tab-issues"):
                yield IssuesTab(self.project_dir)
            with TabPane("Knowledge", id="tab-knowledge"):
                yield KnowledgeTab(self.project_dir)
            with TabPane("Explorer", id="tab-explorer"):
                yield FileExplorerTab(self.project_dir)
            with TabPane("Profiler", id="tab-profile"):
                yield ProfileTab(self.project_dir)
            with TabPane("Logs", id="tab-logs"):
                yield LogsTab()
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        import subprocess

        # Handle dashboard buttons (bubble up)
        if event.button.id == "btn-refresh":
            self.query_one(DashboardTab).update_history()
            self.notify("Dashboard refreshed.")
        elif event.button.id == "btn-test":
            self.notify("Running tests...")
            try:
                subprocess.Popen([sys.executable, "main.py", "test", "-p", str(self.project_dir)])
                self.notify("Tests started in background.")
            except Exception as e:
                self.notify(f"Failed to start tests: {e}", severity="error")
        elif event.button.id == "btn-lint":
            self.notify("Running lint...")
            try:
                subprocess.Popen([sys.executable, "main.py", "lint", "-p", str(self.project_dir)])
                self.notify("Lint started in background.")
            except Exception as e:
                self.notify(f"Failed to start lint: {e}", severity="error")

if __name__ == "__main__":
    # Add parent dir to path to allow direct execution
    import_path = str(Path(__file__).parent.parent)
    sys.path.append(import_path)

    project_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    app = AgentTUI(project_dir=project_path)
    app.run()
