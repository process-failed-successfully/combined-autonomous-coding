import sys
import io
import contextlib
import os
import json
import shlex
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, RichLog, DirectoryTree, TabbedContent, TabPane, Button, Label, Input, DataTable, Select, Markdown, ListView, ListItem, Tree, Checkbox, TextArea
from textual.containers import Container, Horizontal, VerticalScroll, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.binding import Binding
from textual import on
from rich.syntax import Syntax

from shared.cli_utils import get_latest_log_file, get_workflow_stage, get_all_log_files
from shared.knowledge import KnowledgeManager
from shared.ask import run_ask_logic
from shared.optimize import OptimizationManager
from shared.database import init_db
from shared.github_client import GitHubClient
from shared.config_loader import load_config_from_file
from shared.dependencies import DependencyAnalyzer, DependencyUpdater
from shared.task_manager import TaskManager, Task
from shared.debt import DebtCollector
from shared.security import SecurityAuditor
from shared.map import scan_project, CodeNode
from shared.git import get_git_log, get_commit_details
from shared.db_query import get_schema_info, generate_sql, execute_sqlite, is_read_only_query
from shared.search import search_codebase
from shared.work_session import WorkSessionManager, Session
from shared.worktree import WorktreeManager
from shared.recipes import RecipeManager
from shared.secrets import SecretsManager
from shared.api_lab import ApiLabManager
from shared.plan import run_plan_logic

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

class CodeMapTab(Container):
    """Tab for visualizing project structure (Classes, Functions)."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.map_data = {}

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical(id="codemap-left-pane"):
                yield Input(placeholder="Filter nodes...", id="codemap-filter")
                yield Tree("Project Structure", id="codemap-tree")
            with VerticalScroll(id="codemap-right-pane"):
                yield RichLog(id="codemap-preview", markup=True)

    def on_mount(self) -> None:
        self.refresh_map()

    def refresh_map(self) -> None:
        self.map_data = scan_project(self.project_dir)
        self.populate_tree()

    def populate_tree(self, filter_text: str = "") -> None:
        tree = self.query_one("#codemap-tree", Tree)
        tree.clear()
        tree.root.expand()

        for file_path, node in sorted(self.map_data.items()):
            # Apply filter: if filter matches file or any child
            if filter_text and filter_text.lower() not in file_path.lower():
                # Check children
                has_match = any(filter_text.lower() in c.name.lower() for c in node.children)
                if not has_match:
                    continue

            # Add file node
            file_node = tree.root.add(f"📄 {file_path}", data=node, expand=True)

            # Add children
            for child in node.children:
                if filter_text and filter_text.lower() not in child.name.lower() and filter_text.lower() not in file_path.lower():
                    continue

                icon = "C" if child.type == "class" else "F"
                child_node = file_node.add(f"[{icon}] {child.name}", data=child)

                # Grandchildren (methods in class)
                for gc in child.children:
                     if filter_text and filter_text.lower() not in gc.name.lower() and filter_text.lower() not in child.name.lower() and filter_text.lower() not in file_path.lower():
                         continue
                     icon_gc = "M" if gc.type == "function" else "?"
                     child_node.add(f"[{icon_gc}] {gc.name}", data=gc)
                     child_node.expand()

    @on(Input.Changed, "#codemap-filter")
    def on_filter_changed(self, event: Input.Changed) -> None:
        self.populate_tree(event.value)

    @on(Tree.NodeSelected, "#codemap-tree")
    def on_node_selected(self, event: Tree.NodeSelected) -> None:
        node_data = event.node.data
        if not node_data:
            return

        preview = self.query_one("#codemap-preview", RichLog)
        preview.clear()

        try:
            full_path = self.project_dir / node_data.file
            if not full_path.exists():
                preview.write(f"File not found: {full_path}")
                return

            content = full_path.read_text(encoding="utf-8", errors="replace")
            lines = content.splitlines()

            start = node_data.lineno - 1
            end = node_data.end_lineno if node_data.end_lineno else start + 20

            # Clamp end
            end = min(end, len(lines))

            # Extract snippet
            snippet = "\n".join(lines[start:end])

            syntax = Syntax(snippet, "python", theme="monokai", line_numbers=True, start_line=start+1)
            preview.write(f"[bold]{node_data.type.capitalize()}: {node_data.name}[/bold] (Lines {start+1}-{end})")
            preview.write(syntax)

        except Exception as e:
            preview.write(f"Error reading code: {e}")

class LogsTab(Container):
    """Tab for viewing and filtering logs."""

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: Log List
            with Vertical(id="logs-list-container", classes="stat-box"):
                yield Label("[bold]Log Files[/bold]")
                yield ListView(id="log-file-list")
                yield Button("Refresh Logs", id="btn-refresh-logs", variant="default")

            # Right Pane: Log Viewer
            with Vertical(id="logs-view-container"):
                with Horizontal(classes="stat-box"):
                    yield Label("Filter:", classes="label")
                    yield Input(placeholder="Type to filter log lines...", id="log-filter")
                yield RichLog(id="log-viewer", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        self.load_log_files()

    def load_log_files(self) -> None:
        log_list = self.query_one("#log-file-list", ListView)
        log_list.clear()

        logs = get_all_log_files()
        if not logs:
            log_list.append(ListItem(Label("No logs found")))
            return

        for log_file in logs:
            # Format: filename (size)
            try:
                size = log_file.stat().st_size
                size_str = f"{size / 1024:.1f} KB"
                label = f"{log_file.name} ({size_str})"
            except OSError:
                label = log_file.name

            item = ListItem(Label(label))
            # Attach the path to the item for retrieval
            item.log_path = log_file
            log_list.append(item)

        # Select the first one (latest) by default
        if len(log_list.children) > 0:
            log_list.index = 0
            # Manually trigger load as setting index doesn't always fire Selected
            if hasattr(log_list.children[0], "log_path"):
                self.load_log_content(log_list.children[0].log_path)

    @on(ListView.Selected, "#log-file-list")
    def on_log_selected(self, event: ListView.Selected) -> None:
        if hasattr(event.item, "log_path"):
            self.load_log_content(event.item.log_path)

    @on(Input.Changed, "#log-filter")
    def on_filter_changed(self, event: Input.Changed) -> None:
        # We need to reload the CURRENT log file with the new filter.
        if hasattr(self, "current_log_path") and self.current_log_path:
            self.load_log_content(self.current_log_path, filter_text=event.value)

    @on(Button.Pressed, "#btn-refresh-logs")
    def on_refresh_logs(self) -> None:
        self.load_log_files()
        self.notify("Log list refreshed.")

    def load_log_content(self, file_path: Path, filter_text: str = "") -> None:
        self.current_log_path = file_path
        log_viewer = self.query_one("#log-viewer", RichLog)
        log_viewer.clear()

        # Get filter text if not provided (e.g. from state)
        if filter_text == "":
            inp = self.query_one("#log-filter", Input)
            if inp:
                filter_text = inp.value

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

                # Apply filter
                if filter_text:
                    lines = [line for line in lines if filter_text.lower() in line.lower()]

                # Limit to last 2000 lines if too many
                if len(lines) > 2000:
                    log_viewer.write(f"[bold yellow]Displaying last 2000 lines of {len(lines)}...[/bold yellow]")
                    lines = lines[-2000:]

                log_viewer.write("".join(lines))

        except Exception as e:
            log_viewer.write(f"[bold red]Error reading log file:[/bold red] {e}")

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

class TasksTab(Container):
    """Tab for viewing Unified Tasks (GitHub, Jira, Sprint, TODOs)."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.task_manager = TaskManager(project_dir)
        self.tasks_cache = []

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Unified Task Board[/bold]", classes="welcome-text")
            with Horizontal(classes="stat-box"):
                yield Button("Refresh", id="btn-tasks-refresh", variant="primary")
                yield Select.from_values(["All", "GitHub", "Jira", "Sprint", "TODO"], id="select-task-source", value="All")
                yield Input(placeholder="Filter by title...", id="input-task-filter")

            yield DataTable(id="tasks-table")

    def on_mount(self) -> None:
        table = self.query_one("#tasks-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Source", "ID", "Title", "Status", "Priority")
        self.load_tasks()

    def load_tasks(self) -> None:
        table = self.query_one("#tasks-table", DataTable)
        table.clear()
        self.notify("Loading tasks...", timeout=1)

        try:
            tasks = self.task_manager.fetch_all_tasks()
            self.tasks_cache = tasks
            self._update_table(tasks)
            self.notify(f"Loaded {len(tasks)} tasks.")
        except Exception as e:
            self.notify(f"Error fetching tasks: {e}", severity="error")

    def _update_table(self, tasks: list[Task]) -> None:
        table = self.query_one("#tasks-table", DataTable)
        table.clear()

        source_filter = self.query_one("#select-task-source", Select).value or "All"
        filter_text = self.query_one("#input-task-filter", Input).value.lower()

        for task in tasks:
            if source_filter != "All" and task.source.lower() != source_filter.lower():
                continue

            if filter_text and filter_text not in task.title.lower():
                continue

            # Color code status/priority?
            # Textual DataTables use Rich Renderables.

            source_display = task.source.upper()
            status_display = task.status
            priority_display = task.priority

            # Simple color formatting tags
            if task.priority == "High":
                priority_display = f"[red]{task.priority}[/red]"
            elif task.priority == "Low":
                priority_display = f"[green]{task.priority}[/green]"

            table.add_row(source_display, task.id, task.title, status_display, priority_display)

    @on(Button.Pressed, "#btn-tasks-refresh")
    def refresh_tasks(self):
        self.load_tasks()

    @on(Select.Changed, "#select-task-source")
    def filter_source(self):
        self._update_table(self.tasks_cache)

    @on(Input.Changed, "#input-task-filter")
    def filter_text(self):
        self._update_table(self.tasks_cache)

class GitTab(Container):
    """Tab for viewing Git history."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical(id="git-list-container", classes="stat-box"):
                yield Label("[bold]Git History[/bold]")
                yield DataTable(id="git-log-table")
                yield Button("Refresh", id="btn-refresh-git", variant="default")

            with Vertical(id="git-details-container"):
                yield Label("[bold]Commit Details[/bold]")
                yield RichLog(id="git-details-view", wrap=True, highlight=True, markup=False)

    def on_mount(self) -> None:
        table = self.query_one("#git-log-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Hash", "Date", "Author", "Message")
        self.load_history()

    def load_history(self) -> None:
        table = self.query_one("#git-log-table", DataTable)
        table.clear()

        logs = get_git_log(self.project_dir)
        for log in logs:
            table.add_row(
                log["hash"],
                log["date"],
                log["author"],
                log["message"]
            )

    @on(Button.Pressed, "#btn-refresh-git")
    def on_refresh(self) -> None:
        self.load_history()
        self.notify("Git history refreshed.")

    @on(DataTable.RowSelected, "#git-log-table")
    def on_row_selected(self, event: DataTable.RowSelected) -> None:
        table = self.query_one("#git-log-table", DataTable)
        row_values = table.get_row(event.row_key)
        commit_hash = row_values[0]

        details = get_commit_details(self.project_dir, commit_hash)
        viewer = self.query_one("#git-details-view", RichLog)
        viewer.clear()
        viewer.write(details)

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

class DependenciesTab(Container):
    """Tab for managing dependencies."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.analyzer = DependencyAnalyzer(project_dir)
        self.updater = DependencyUpdater(project_dir)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Project Dependencies[/bold]", classes="welcome-text")
            yield DataTable(id="deps-table")
            with Horizontal(classes="stat-box"):
                yield Button("Refresh", id="btn-deps-refresh", variant="default")
                yield Button("Check Updates", id="btn-deps-check", variant="primary")
            yield Label("", id="deps-status")

    def on_mount(self) -> None:
        table = self.query_one("#deps-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Language", "Package", "Version", "Type", "Latest", "Status")
        self.load_deps()

    def load_deps(self) -> None:
        table = self.query_one("#deps-table", DataTable)
        table.clear()

        try:
            data = self.analyzer.scan()

            # Python
            for file_info in data.get("python", []):
                for dep in file_info.get("dependencies", []):
                    table.add_row(
                        "Python",
                        dep["name"],
                        dep.get("version", ""),
                        "prod",
                        dep.get("latest", "-"),
                        "Outdated" if dep.get("outdated") else "OK"
                    )

            # Node
            for file_info in data.get("node", []):
                for dep in file_info.get("dependencies", []):
                    table.add_row(
                        "Node",
                        dep["name"],
                        dep.get("version", ""),
                        dep.get("type", "prod"),
                        dep.get("latest", "-"),
                        "Outdated" if dep.get("outdated") else "OK"
                    )

            self.query_one("#deps-status", Label).update("Dependencies loaded.")
        except Exception as e:
            self.notify(f"Error loading dependencies: {e}", severity="error")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-deps-refresh":
            self.load_deps()
            self.notify("Dependencies refreshed.")
        elif event.button.id == "btn-deps-check":
            await self.check_updates()

    async def check_updates(self):
        self.query_one("#deps-status", Label).update("Checking for updates... (this may take a while)")
        self.notify("Checking updates...", severity="information")

        # Run potentially blocking check_updates in a thread
        import asyncio

        try:
            # We need to re-scan and then check updates
            def do_check():
                data = self.analyzer.scan()
                return self.analyzer.check_updates(data)

            data = await asyncio.to_thread(do_check)

            # Update table with new data
            table = self.query_one("#deps-table", DataTable)
            table.clear()

            # Python
            for file_info in data.get("python", []):
                for dep in file_info.get("dependencies", []):
                    status = "[red]Outdated[/red]" if dep.get("outdated") else "[green]OK[/green]"
                    table.add_row(
                        "Python",
                        dep["name"],
                        dep.get("version", ""),
                        "prod",
                        dep.get("latest", "-"),
                        status
                    )

            # Node
            for file_info in data.get("node", []):
                for dep in file_info.get("dependencies", []):
                    status = "[red]Outdated[/red]" if dep.get("outdated") else "[green]OK[/green]"
                    table.add_row(
                        "Node",
                        dep["name"],
                        dep.get("version", ""),
                        dep.get("type", "prod"),
                        dep.get("latest", "-"),
                        status
                    )

            self.query_one("#deps-status", Label).update("Update check complete.")
            self.notify("Update check complete.")

        except Exception as e:
            self.notify(f"Error checking updates: {e}", severity="error")
            self.query_one("#deps-status", Label).update("Error checking updates.")


def collect_analytics_data(project_dir: Path) -> dict:
    """Collects analytics data for the dashboard."""
    debt_collector = DebtCollector(project_dir)
    security_auditor = SecurityAuditor(project_dir)

    # Debt
    debt_metrics = debt_collector.collect()
    debt_score, debt_grade = debt_collector.calculate_score(debt_metrics)

    # Security
    security_findings = security_auditor.scan_secrets()

    return {
        "debt": {"metrics": debt_metrics, "score": debt_score, "grade": debt_grade},
        "security": security_findings
    }


class AnalyticsTab(Container):
    """Tab for project health and analytics."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Label("[bold]Project Analytics & Health[/bold]", classes="welcome-text")

            # Technical Debt Section
            with Container(classes="stat-box"):
                yield Label("[bold]Technical Debt[/bold]")
                yield Label("Loading...", id="debt-summary")
                yield DataTable(id="debt-table")

            # Security Section
            with Container(classes="stat-box"):
                yield Label("[bold]Security Audit[/bold]")
                yield Label("Loading...", id="security-summary")
                yield DataTable(id="security-table")

            # Actions
            with Horizontal(classes="stat-box"):
                yield Button("Refresh Analysis", id="btn-refresh-analytics", variant="primary")
                yield Label("", id="analytics-status")

    def on_mount(self) -> None:
        # Debt Table
        debt_table = self.query_one("#debt-table", DataTable)
        debt_table.add_columns("Metric", "Count", "Details")

        # Security Table
        sec_table = self.query_one("#security-table", DataTable)
        sec_table.add_columns("Severity", "Type", "Description", "Location")

        # Trigger load
        self.refresh_analytics()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-refresh-analytics":
            self.refresh_analytics()

    def refresh_analytics(self) -> None:
        self.query_one("#analytics-status", Label).update("Analyzing... (this may take a few seconds)")
        self.notify("Starting analysis...")

        # Run in thread
        import asyncio
        asyncio.create_task(self._run_analysis())

    async def _run_analysis(self) -> None:
        import asyncio

        try:
            # Run the extracted function in a thread
            data = await asyncio.to_thread(collect_analytics_data, self.project_dir)
            self._update_ui(data)
            self.query_one("#analytics-status", Label).update("Analysis complete.")
            self.notify("Analysis complete.")
        except Exception as e:
            self.query_one("#analytics-status", Label).update(f"Error: {e}")
            self.notify(f"Analysis failed: {e}", severity="error")

    def _update_ui(self, data: dict) -> None:
        # Update Debt
        debt = data["debt"]
        metrics = debt["metrics"]
        score = debt["score"]
        grade = debt["grade"]

        # Color for grade
        grade_color = "green"
        if grade in ["B", "C"]:
            grade_color = "yellow"
        if grade in ["D", "F"]:
            grade_color = "red"

        summary = f"Grade: [{grade_color}]{grade}[/{grade_color}] (Score: {int(score)})"
        self.query_one("#debt-summary", Label).update(summary)

        debt_table = self.query_one("#debt-table", DataTable)
        debt_table.clear()
        debt_table.add_row("TODOs", str(metrics["todos"]["count"]), "Pending tasks")
        debt_table.add_row("Complexity Risks", str(metrics["complexity"]["high_risk_count"]), f"Avg: {metrics['complexity']['average']:.1f}")
        debt_table.add_row("Duplication", f"{metrics['duplication']['blocks']} blocks", f"{metrics['duplication']['total_tokens']} tokens")
        debt_table.add_row("Unused Code", str(metrics['unused']['count']), "Definitions")

        # Update Security
        findings = data["security"]
        high_count = sum(1 for f in findings if f["severity"] == "HIGH")
        medium_count = sum(1 for f in findings if f["severity"] == "MEDIUM")

        sec_summary = f"Issues Found: [red]{high_count} High[/red], [yellow]{medium_count} Medium[/yellow], {len(findings) - high_count - medium_count} Low"
        if not findings:
            sec_summary = "[green]No secrets or dangerous patterns found.[/green]"

        self.query_one("#security-summary", Label).update(sec_summary)

        sec_table = self.query_one("#security-table", DataTable)
        sec_table.clear()

        # Sort by severity
        severity_map = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        findings.sort(key=lambda x: severity_map.get(x["severity"], 3))

        for f in findings[:20]:  # Limit to top 20
            sev = f["severity"]
            if sev == "HIGH":
                sev = f"[red]{sev}[/red]"
            elif sev == "MEDIUM":
                sev = f"[yellow]{sev}[/yellow]"

            location = f"{f['file']}:{f['line']}"
            sec_table.add_row(sev, f["type"], f["description"], location)


class SecretsTab(Container):
    """Tab for managing encrypted secrets."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = SecretsManager(project_dir)
        self.key_exists = False

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Secrets Manager[/bold]", classes="welcome-text")

            # Initialization Status
            with Horizontal(id="secret-init-container", classes="stat-box"):
                yield Label("Status: ", id="lbl-secret-status")
                yield Button("Initialize Key", id="btn-secret-init", variant="warning", disabled=True)

            with Horizontal():
                # Left Pane: Secrets List
                with Vertical(id="secrets-list-container", classes="stat-box"):
                    yield Label("[bold]Secrets[/bold]")
                    yield ListView(id="secrets-list")
                    yield Button("Refresh", id="btn-secret-refresh", variant="default")

                # Right Pane: Actions
                with Vertical(id="secret-actions-container"):
                    yield Label("[bold]Manage Secrets[/bold]")

                    with Container(classes="stat-box"):
                        yield Label("Add / Update Secret")
                        yield Input(placeholder="Name (e.g. API_KEY)...", id="secret-name-input")
                        yield Input(placeholder="Value...", id="secret-value-input", password=True)
                        yield Checkbox("Show Value", id="chk-show-secret")
                        yield Button("Set Secret", id="btn-secret-add", variant="primary")

                    with Container(classes="stat-box"):
                        yield Label("Actions on Selected Secret")
                        yield Button("Delete Selected", id="btn-secret-delete", variant="error", disabled=True)

    def on_mount(self) -> None:
        self.check_key()

    def check_key(self) -> None:
        self.key_exists = self.manager.key_path.exists()
        lbl = self.query_one("#lbl-secret-status", Label)
        btn = self.query_one("#btn-secret-init", Button)

        if self.key_exists:
            lbl.update("[green]Encryption Key Active[/green]")
            btn.disabled = True
            self.load_secrets()
        else:
            lbl.update("[red]No Encryption Key Found[/red]")
            btn.disabled = False
            self.query_one("#secrets-list", ListView).clear()

    def load_secrets(self) -> None:
        if not self.key_exists:
            return

        secrets_list = self.query_one("#secrets-list", ListView)
        secrets_list.clear()

        try:
            names = self.manager.list_secrets()
            for name in names:
                secrets_list.append(ListItem(Label(name)))
        except Exception as e:
            self.notify(f"Error loading secrets: {e}", severity="error")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-secret-init":
            self.init_key()
        elif event.button.id == "btn-secret-refresh":
            self.check_key()
        elif event.button.id == "btn-secret-add":
            self.add_secret()
        elif event.button.id == "btn-secret-delete":
            self.delete_secret()

    def init_key(self) -> None:
        try:
            if self.manager.generate_key():
                self.notify("Encryption key generated.")
                self.check_key()
            else:
                self.notify("Key already exists.", severity="warning")
        except Exception as e:
             self.notify(f"Error generating key: {e}", severity="error")

    def add_secret(self) -> None:
        if not self.key_exists:
            self.notify("Initialize key first.", severity="error")
            return

        name = self.query_one("#secret-name-input", Input).value
        value = self.query_one("#secret-value-input", Input).value

        if not name or not value:
            self.notify("Name and value required.", severity="error")
            return

        try:
            self.manager.set_secret(name, value)
            self.notify(f"Secret '{name}' set.")
            self.query_one("#secret-name-input", Input).value = ""
            self.query_one("#secret-value-input", Input).value = ""
            self.load_secrets()
        except Exception as e:
            self.notify(f"Error setting secret: {e}", severity="error")

    def delete_secret(self) -> None:
        secrets_list = self.query_one("#secrets-list", ListView)
        if secrets_list.index is None:
            return

        item = secrets_list.children[secrets_list.index]
        label = item.query_one(Label)
        name = str(label.renderable)

        try:
            if self.manager.delete_secret(name):
                self.notify(f"Deleted secret '{name}'")
                self.load_secrets()
            else:
                self.notify(f"Secret '{name}' not found.", severity="error")
        except Exception as e:
            self.notify(f"Error deleting secret: {e}", severity="error")

    @on(ListView.Selected, "#secrets-list")
    def on_secret_selected(self) -> None:
        self.query_one("#btn-secret-delete").disabled = False

    @on(Checkbox.Changed, "#chk-show-secret")
    def on_show_secret_changed(self, event: Checkbox.Changed) -> None:
        inp = self.query_one("#secret-value-input", Input)
        inp.password = not event.value


class DatabaseTab(Container):
    """Tab for database management."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.db_path = None
        self.schema = ""

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Database Manager[/bold]", classes="welcome-text")

            with Horizontal(classes="stat-box"):
                yield Button("Detect DB", id="btn-db-detect", variant="primary")
                yield Label("No DB selected", id="lbl-db-status")

            with Horizontal():
                # Schema View
                with Vertical(id="db-schema-container", classes="stat-box"):
                    yield Label("[bold]Schema[/bold]")
                    yield RichLog(id="db-schema-view", wrap=True, highlight=True)

                # Query View
                with Vertical(id="db-query-container"):
                    with Horizontal(classes="stat-box"):
                        yield Select.from_values(["SQL", "Natural Language"], id="select-query-mode", value="SQL")
                        yield Select.from_values(["gemini", "cursor", "local"], id="select-db-agent", value="gemini")

                    yield Checkbox("Allow Write Operations", id="chk-db-write", value=False)
                    yield Input(placeholder="Enter SQL query...", id="input-db-query")
                    yield Button("Execute", id="btn-db-execute", variant="success")

                    yield DataTable(id="db-results-table")
                    yield Label("", id="lbl-query-status")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-db-detect":
            self.detect_db()
        elif event.button.id == "btn-db-execute":
            await self.execute_query()

    def detect_db(self) -> None:
        self.schema, self.db_path = get_schema_info(self.project_dir)
        lbl = self.query_one("#lbl-db-status", Label)
        schema_view = self.query_one("#db-schema-view", RichLog)
        schema_view.clear()

        if self.db_path:
            lbl.update(f"Connected: {self.db_path.name}")
            schema_view.write(self.schema)
            self.notify("Database detected.")
        else:
            lbl.update("No SQLite DB found.")
            schema_view.write("No schema available.")
            self.notify("No database found.", severity="warning")

    async def execute_query(self) -> None:
        if not self.db_path:
            self.notify("No database connected.", severity="error")
            return

        query = self.query_one("#input-db-query", Input).value
        if not query:
            return

        mode = self.query_one("#select-query-mode", Select).value
        status_lbl = self.query_one("#lbl-query-status", Label)
        status_lbl.update("Executing...")

        sql = query
        if mode == "Natural Language":
            status_lbl.update("Generating SQL...")
            agent_type = self.query_one("#select-db-agent", Select).value
            try:
                sql = await generate_sql(query, self.schema, self.project_dir, agent_type=agent_type)
                if sql.startswith("ERROR:"):
                    status_lbl.update("Error generating SQL.")
                    self.notify(sql, severity="error")
                    return

                # Update input with generated SQL and switch to SQL mode
                self.query_one("#input-db-query", Input).value = sql
                self.query_one("#select-query-mode", Select).value = "SQL"
                self.notify(f"SQL generated. Review and execute.")
                status_lbl.update("SQL Generated. Ready to execute.")
                return  # Stop here, don't execute
            except Exception as e:
                status_lbl.update("AI Error.")
                self.notify(f"AI Error: {e}", severity="error")
                return

        # Safety Check
        is_safe = is_read_only_query(sql)
        allow_write = self.query_one("#chk-db-write", Checkbox).value

        if not is_safe and not allow_write:
            status_lbl.update("Operation blocked.")
            self.notify("Write operation blocked! Enable 'Allow Write Operations' to proceed.", severity="error", timeout=5)
            return

        # Execute SQL
        try:
            status_lbl.update("Running SQL...")
            # Run in thread to avoid blocking UI
            import asyncio
            columns, rows, rowcount = await asyncio.to_thread(execute_sqlite, self.db_path, sql)

            table = self.query_one("#db-results-table", DataTable)
            table.clear(columns=True)

            if columns:
                table.add_columns(*columns)
                table.add_rows(rows)
                status_lbl.update(f"Returned {len(rows)} rows.")
            else:
                status_lbl.update(f"Executed. Rows affected: {rowcount}")

        except Exception as e:
            status_lbl.update("Execution Error.")
            self.notify(f"SQL Error: {e}", severity="error")


class SearchTab(Container):
    """Tab for searching code (Grep)."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        with Horizontal(classes="stat-box"):
            yield Input(placeholder="Search pattern...", id="search-input")
            yield Button("Search", id="btn-search", variant="primary")

        with Horizontal(classes="stat-box"):
            yield Checkbox("Case Sensitive", id="chk-case")
            yield Checkbox("Regex", id="chk-regex")
            yield Input(placeholder="File pattern (e.g. *.py)", id="file-pattern-input")

        with Horizontal():
            with Vertical(id="search-results-pane"):
                yield DataTable(id="search-results-table")
            with VerticalScroll(id="search-preview-pane"):
                yield RichLog(id="search-preview", markup=True)

    def on_mount(self) -> None:
        table = self.query_one("#search-results-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("File", "Line", "Content")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-search":
            await self.perform_search()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "search-input":
            await self.perform_search()

    async def perform_search(self) -> None:
        query = self.query_one("#search-input", Input).value
        if not query:
            return

        case_sensitive = self.query_one("#chk-case", Checkbox).value
        is_regex = self.query_one("#chk-regex", Checkbox).value
        file_pattern = self.query_one("#file-pattern-input", Input).value

        table = self.query_one("#search-results-table", DataTable)
        table.clear()
        self.notify("Searching...")

        import asyncio
        try:
            # Run in thread
            results = await asyncio.to_thread(
                search_codebase,
                self.project_dir,
                query,
                file_pattern=file_pattern if file_pattern else None,
                case_sensitive=case_sensitive,
                is_regex=is_regex,
                context_lines=2
            )

            self.results_cache = results

            if not results:
                self.notify("No matches found.")
                return

            self.notify(f"Found {len(results)} matches.")
            for i, res in enumerate(results):
                table.add_row(
                    res["file"],
                    str(res["line"]),
                    res["content"],
                    key=str(i) # Store index as key
                )
        except Exception as e:
            self.notify(f"Search error: {e}", severity="error")

    @on(DataTable.RowSelected, "#search-results-table")
    def on_result_selected(self, event: DataTable.RowSelected) -> None:
        if not hasattr(self, "results_cache"):
            return

        try:
            index = int(event.row_key.value)
            result = self.results_cache[index]

            preview = self.query_one("#search-preview", RichLog)
            preview.clear()

            preview.write(f"[bold]{result['file']}:{result['line']}[/bold]")

            # Show context
            for line in result.get("context_before", []):
                preview.write(f"[dim]{line}[/dim]")

            preview.write(f"[bold yellow]{result['line']}: {result['content']}[/bold yellow]")

            for line in result.get("context_after", []):
                preview.write(f"[dim]{line}[/dim]")

        except Exception as e:
             self.notify(f"Preview error: {e}", severity="error")


class SessionTab(Container):
    """Tab for managing work sessions."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = WorkSessionManager(project_dir)
        self.current_session_name = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: Session List
            with Vertical(id="session-list-container", classes="stat-box"):
                yield Label("[bold]Sessions[/bold]")
                yield DataTable(id="session-table")
                with Horizontal():
                    yield Input(placeholder="New session name...", id="new-session-input")
                    yield Button("Create", id="btn-create-session", variant="primary")
                yield Button("Refresh", id="btn-refresh-sessions", variant="default")

            # Right Pane: Session Details
            with Vertical(id="session-details-container"):
                yield Label("[bold]Session Details[/bold]")
                yield Label("Select a session to view details.", id="session-header")

                with TabbedContent():
                    with TabPane("Files"):
                        with Horizontal():
                            yield Input(placeholder="Add file path...", id="add-file-input")
                            yield Button("Add File", id="btn-add-file", variant="success")
                        yield ListView(id="session-files-list")
                        yield Button("Remove Selected File", id="btn-remove-file", variant="error")

                    with TabPane("Notes"):
                        with Horizontal():
                            yield Input(placeholder="Add note...", id="add-note-input")
                            yield Button("Add Note", id="btn-add-note", variant="success")
                        yield RichLog(id="session-notes-log", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        table = self.query_one("#session-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Name", "Updated", "Description")
        self.load_sessions()

    def load_sessions(self) -> None:
        table = self.query_one("#session-table", DataTable)
        table.clear()

        sessions = self.manager.list_sessions()
        active = self.manager.get_active_session()
        active_name = active.name if active else None

        for s in sessions:
            name = s["name"]
            if name == active_name:
                name_display = f"[green]● {name}[/green]"
            else:
                name_display = name

            table.add_row(
                name_display,
                s["updated_at"],
                s.get("description", ""),
                key=name # Store raw name as key
            )

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-refresh-sessions":
            self.load_sessions()
        elif event.button.id == "btn-create-session":
            await self.create_session()
        elif event.button.id == "btn-add-file":
            await self.add_file()
        elif event.button.id == "btn-add-note":
            await self.add_note()
        elif event.button.id == "btn-remove-file":
            await self.remove_file()

    async def create_session(self) -> None:
        inp = self.query_one("#new-session-input", Input)
        name = inp.value
        if not name:
            self.notify("Session name required.", severity="error")
            return

        try:
            self.manager.create(name)
            self.notify(f"Session '{name}' created.")
            inp.value = ""
            self.load_sessions()
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    @on(DataTable.RowSelected, "#session-table")
    def on_session_selected(self, event: DataTable.RowSelected) -> None:
        # Key was stored as raw name
        name = event.row_key.value
        self.load_session_details(name)

    def load_session_details(self, name: str) -> None:
        self.current_session_name = name
        session = self.manager.load_session(name)
        if not session:
            self.notify("Session not found.", severity="error")
            return

        header = self.query_one("#session-header", Label)
        header.update(f"[bold]{session.name}[/bold] (Created: {session.created_at})")

        # Files
        files_list = self.query_one("#session-files-list", ListView)
        files_list.clear()
        for f in session.files:
            files_list.append(ListItem(Label(f)))

        # Notes
        notes_log = self.query_one("#session-notes-log", RichLog)
        notes_log.clear()
        for n in session.notes:
            notes_log.write(n)

    async def add_file(self) -> None:
        if not self.current_session_name:
            self.notify("No session selected.", severity="warning")
            return

        inp = self.query_one("#add-file-input", Input)
        path = inp.value
        if not path:
            return

        try:
            self.manager.add_file(self.current_session_name, path)
            self.notify("File added.")
            inp.value = ""
            self.load_session_details(self.current_session_name)
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    async def add_note(self) -> None:
        if not self.current_session_name:
            self.notify("No session selected.", severity="warning")
            return

        inp = self.query_one("#add-note-input", Input)
        note = inp.value
        if not note:
            return

        try:
            self.manager.add_note(self.current_session_name, note)
            self.notify("Note added.")
            inp.value = ""
            self.load_session_details(self.current_session_name)
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    async def remove_file(self) -> None:
         if not self.current_session_name:
            return

         files_list = self.query_one("#session-files-list", ListView)
         if files_list.index is not None:
             item = files_list.children[files_list.index]
             # Extract text from Label inside ListItem
             label = item.query_one(Label)
             path = str(label.renderable)

             try:
                 self.manager.remove_file(self.current_session_name, path)
                 self.notify(f"Removed {path}")
                 self.load_session_details(self.current_session_name)
             except Exception as e:
                 self.notify(f"Error: {e}", severity="error")


class RecipesTab(Container):
    """Tab for managing recipes (macros)."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = RecipeManager(project_dir)
        self.selected_recipe = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: List and Create
            with Vertical(id="recipe-list-container", classes="stat-box"):
                yield Label("[bold]Recipes[/bold]")
                yield DataTable(id="recipe-table")

                with Horizontal():
                    yield Input(placeholder="Name...", id="recipe-new-name")
                    yield Input(placeholder="Steps (comma-separated)...", id="recipe-new-steps")
                yield Button("Create Recipe", id="btn-recipe-create", variant="primary")

                yield Button("Refresh", id="btn-recipe-refresh", variant="default")

            # Right Pane: Details and Actions
            with Vertical(id="recipe-details-container"):
                yield Label("[bold]Recipe Details[/bold]")
                yield Label("Select a recipe to view details.", id="recipe-header")

                yield RichLog(id="recipe-log", wrap=True, highlight=True, markup=True)

                with Horizontal(id="recipe-actions"):
                    yield Button("Run", id="btn-recipe-run", variant="success", disabled=True)
                    yield Button("Delete", id="btn-recipe-delete", variant="error", disabled=True)

    def on_mount(self) -> None:
        table = self.query_one("#recipe-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Name", "Steps")
        self.load_recipes()

    def load_recipes(self) -> None:
        table = self.query_one("#recipe-table", DataTable)
        table.clear()

        recipes = self.manager.list_recipes()
        for name, steps in recipes.items():
            steps_preview = ", ".join(steps)
            if len(steps_preview) > 30:
                steps_preview = steps_preview[:27] + "..."
            table.add_row(name, steps_preview, key=name)

    @on(DataTable.RowSelected, "#recipe-table")
    def on_recipe_selected(self, event: DataTable.RowSelected) -> None:
        name = event.row_key.value
        self.selected_recipe = name
        self.update_details(name)

        # Enable buttons
        self.query_one("#btn-recipe-run").disabled = False
        self.query_one("#btn-recipe-delete").disabled = False

    def update_details(self, name: str) -> None:
        header = self.query_one("#recipe-header", Label)
        header.update(f"[bold]{name}[/bold]")

        log = self.query_one("#recipe-log", RichLog)
        log.clear()

        steps = self.manager.get_recipe(name)
        if steps:
            log.write("[bold]Steps:[/bold]")
            for i, step in enumerate(steps):
                log.write(f"  {i+1}. {step}")
        else:
             log.write("Recipe not found.")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-recipe-refresh":
            self.load_recipes()
            self.notify("Recipes refreshed.")

        elif event.button.id == "btn-recipe-create":
            await self.create_recipe()

        elif event.button.id == "btn-recipe-run":
            await self.run_recipe()

        elif event.button.id == "btn-recipe-delete":
            await self.delete_recipe()

    async def create_recipe(self) -> None:
        name_inp = self.query_one("#recipe-new-name", Input)
        steps_inp = self.query_one("#recipe-new-steps", Input)

        name = name_inp.value
        steps_str = steps_inp.value

        if not name or not steps_str:
            self.notify("Name and steps required.", severity="error")
            return

        steps = [s.strip() for s in steps_str.split(",") if s.strip()]

        if not steps:
             self.notify("At least one step required.", severity="error")
             return

        try:
            self.manager.add_recipe(name, steps)
            self.notify(f"Recipe '{name}' created.")
            name_inp.value = ""
            steps_inp.value = ""
            self.load_recipes()
        except Exception as e:
            self.notify(f"Error creating recipe: {e}", severity="error")

    async def run_recipe(self) -> None:
        if not self.selected_recipe:
            return

        log = self.query_one("#recipe-log", RichLog)
        log.write(f"\\n[bold green]Running '{self.selected_recipe}'...[/bold green]")
        self.notify(f"Running recipe '{self.selected_recipe}'...")

        import asyncio

        success = False
        output = ""

        def run_in_thread():
             return self.manager.run_recipe(self.selected_recipe, capture_output=True)

        try:
             success, output = await asyncio.to_thread(run_in_thread)
        except Exception as e:
             log.write(f"[bold red]Execution Error:[/bold red] {e}")

        log.write(output)

        if success:
             log.write(f"[bold green]Recipe '{self.selected_recipe}' completed.[/bold green]")
             self.notify("Recipe completed.")
        else:
             log.write(f"[bold red]Recipe '{self.selected_recipe}' failed.[/bold red]")
             self.notify("Recipe failed.", severity="error")

    async def delete_recipe(self) -> None:
        if not self.selected_recipe:
            return

        try:
            self.manager.delete_recipe(self.selected_recipe)
            self.notify(f"Recipe '{self.selected_recipe}' deleted.")
            self.selected_recipe = None
            self.load_recipes()

            # Reset UI
            self.query_one("#recipe-header", Label).update("Select a recipe to view details.")
            self.query_one("#recipe-log", RichLog).clear()
            self.query_one("#btn-recipe-run").disabled = True
            self.query_one("#btn-recipe-delete").disabled = True

        except Exception as e:
            self.notify(f"Error removing recipe: {e}", severity="error")


class WorktreesTab(Container):
    """Tab for managing git worktrees."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = WorktreeManager(project_dir)
        self.selected_worktree = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: List and Create
            with Vertical(id="worktree-list-container", classes="stat-box"):
                yield Label("[bold]Worktrees[/bold]")
                yield DataTable(id="worktree-table")

                with Horizontal():
                    yield Input(placeholder="New worktree name...", id="worktree-new-name")
                    yield Button("Create", id="btn-worktree-create", variant="primary")

                yield Button("Refresh", id="btn-worktree-refresh", variant="default")

            # Right Pane: Details and Actions
            with Vertical(id="worktree-details-container"):
                yield Label("[bold]Worktree Details[/bold]")
                yield Label("Select a worktree to view details.", id="worktree-header")

                yield RichLog(id="worktree-log", wrap=True, highlight=True, markup=True)

                with Horizontal(id="worktree-actions"):
                    yield Button("Status", id="btn-worktree-status", disabled=True)
                    yield Button("Diff (vs HEAD)", id="btn-worktree-diff", disabled=True)
                    yield Button("Remove", id="btn-worktree-remove", variant="error", disabled=True)

    def on_mount(self) -> None:
        table = self.query_one("#worktree-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Name", "Branch")
        self.load_worktrees()

    def load_worktrees(self) -> None:
        table = self.query_one("#worktree-table", DataTable)
        table.clear()

        worktrees = self.manager.list_worktrees()
        for wt in worktrees:
            name = wt.get("name", "Unknown")
            branch = wt.get("branch", "detached").replace("refs/heads/", "")
            table.add_row(name, branch, key=name)

    @on(DataTable.RowSelected, "#worktree-table")
    def on_worktree_selected(self, event: DataTable.RowSelected) -> None:
        name = event.row_key.value
        self.selected_worktree = name
        self.update_details(name)

        # Enable buttons
        self.query_one("#btn-worktree-status").disabled = False
        self.query_one("#btn-worktree-diff").disabled = False
        self.query_one("#btn-worktree-remove").disabled = False

    def update_details(self, name: str) -> None:
        header = self.query_one("#worktree-header", Label)
        header.update(f"[bold]{name}[/bold]")

        log = self.query_one("#worktree-log", RichLog)
        log.clear()
        log.write(f"Selected worktree: {name}")
        log.write("Click buttons below to perform actions.")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-worktree-refresh":
            self.load_worktrees()
            self.notify("Worktrees refreshed.")

        elif event.button.id == "btn-worktree-create":
            await self.create_worktree()

        elif event.button.id == "btn-worktree-status":
            await self.show_status()

        elif event.button.id == "btn-worktree-diff":
            await self.show_diff()

        elif event.button.id == "btn-worktree-remove":
            await self.remove_worktree()

    async def create_worktree(self) -> None:
        inp = self.query_one("#worktree-new-name", Input)
        name = inp.value
        if not name:
            self.notify("Name required.", severity="error")
            return

        self.notify(f"Creating worktree '{name}'...")
        try:
            import asyncio
            await asyncio.to_thread(self.manager.create, name)
            self.notify(f"Worktree '{name}' created.")
            inp.value = ""
            self.load_worktrees()
        except Exception as e:
            self.notify(f"Error creating worktree: {e}", severity="error")

    async def show_status(self) -> None:
        if not self.selected_worktree:
            return

        log = self.query_one("#worktree-log", RichLog)
        log.clear()
        log.write("Fetching status...")

        import asyncio
        status = await asyncio.to_thread(self.manager.get_status, self.selected_worktree)
        log.clear()
        if status.strip():
            log.write("[bold red]Uncommitted Changes:[/bold red]")
            log.write(status)
        else:
            log.write("[green]Clean working directory.[/green]")

    async def show_diff(self) -> None:
        if not self.selected_worktree:
            return

        log = self.query_one("#worktree-log", RichLog)
        log.clear()
        log.write("Fetching diff...")

        import asyncio
        diff = await asyncio.to_thread(self.manager.diff, self.selected_worktree)
        log.clear()
        if diff.strip():
            log.write(Syntax(diff, "diff", theme="monokai"))
        else:
            log.write("[green]No differences with HEAD.[/green]")

    async def remove_worktree(self) -> None:
        if not self.selected_worktree:
            return

        try:
            self.manager.remove(self.selected_worktree, force=True)
            self.notify(f"Worktree '{self.selected_worktree}' removed.")
            self.selected_worktree = None
            self.load_worktrees()

            # Reset UI
            self.query_one("#worktree-header", Label).update("Select a worktree to view details.")
            self.query_one("#worktree-log", RichLog).clear()
            self.query_one("#btn-worktree-status").disabled = True
            self.query_one("#btn-worktree-diff").disabled = True
            self.query_one("#btn-worktree-remove").disabled = True

        except Exception as e:
            self.notify(f"Error removing worktree: {e}", severity="error")


class ApiLabTab(Container):
    """Tab for API experimentation."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = ApiLabManager(project_dir)
        self.selected_endpoint = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: Endpoint List
            with Vertical(id="api-list-container", classes="stat-box"):
                yield Label("[bold]Endpoints[/bold]")
                yield ListView(id="api-endpoint-list")
                with Horizontal():
                    yield Button("Load Spec", id="btn-api-load", variant="primary")
                    yield Button("Generate", id="btn-api-generate", variant="warning")

            # Right Pane: Request/Response
            with Vertical(id="api-details-container"):
                yield Label("[bold]Request Builder[/bold]")

                # Request Line
                with Horizontal(classes="stat-box"):
                    yield Select.from_values(["GET", "POST", "PUT", "DELETE", "PATCH"], id="api-method", value="GET")
                    yield Input(placeholder="URL...", id="api-url")
                    yield Button("Send", id="btn-api-send", variant="success")

                # Body
                with Vertical(classes="stat-box"):
                    yield Label("Request Body (JSON):")
                    yield Input(placeholder="{ ... }", id="api-body")

                # Response
                yield Label("[bold]Response[/bold]")
                yield RichLog(id="api-response-log", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        self.load_spec()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-api-load":
            self.load_spec(force_reload=True)
        elif event.button.id == "btn-api-generate":
            await self.generate_spec()
        elif event.button.id == "btn-api-send":
            await self.send_request()

    def load_spec(self, force_reload: bool = False) -> None:
        if not self.manager.spec_data or force_reload:
            if self.manager.load_spec():
                self.notify("OpenAPI spec loaded.")
            else:
                self.notify("No OpenAPI spec found.", severity="warning")
                return

        endpoints = self.manager.list_endpoints()
        list_view = self.query_one("#api-endpoint-list", ListView)
        list_view.clear()

        for ep in endpoints:
            method = ep['method']
            path = ep['path']
            # Color code method
            if method == "GET": method_fmt = f"[blue]{method}[/blue]"
            elif method == "POST": method_fmt = f"[green]{method}[/green]"
            elif method == "DELETE": method_fmt = f"[red]{method}[/red]"
            else: method_fmt = f"[yellow]{method}[/yellow]"

            label = f"{method_fmt} {path}"
            item = ListItem(Label(label, markup=True))
            # Store data in item (monkey patch for simplicity as ListItem data is strictly renderable)
            item.endpoint_data = ep
            list_view.append(item)

        # Set Base URL if empty
        url_input = self.query_one("#api-url", Input)
        if not url_input.value:
            base = self.manager.get_server_url()
            url_input.value = base

    async def generate_spec(self) -> None:
        self.notify("Generating OpenAPI spec... (this takes time)")
        from shared.openapi import OpenAPIGenerator
        import asyncio

        generator = OpenAPIGenerator(self.project_dir)
        output_path = self.project_dir / "openapi.yaml"

        success = await generator.generate(output_path)
        if success:
            self.notify("Spec generated.")
            self.load_spec(force_reload=True)
        else:
            self.notify("Failed to generate spec.", severity="error")

    @on(ListView.Selected, "#api-endpoint-list")
    def on_endpoint_selected(self, event: ListView.Selected) -> None:
        if hasattr(event.item, "endpoint_data"):
            data = event.item.endpoint_data

            # Update Method
            self.query_one("#api-method", Select).value = data['method']

            # Update URL (append path to base)
            base = self.manager.get_server_url()
            path = data['path']
            # Simple join
            if base.endswith("/") and path.startswith("/"):
                full_url = base + path[1:]
            elif not base.endswith("/") and not path.startswith("/"):
                full_url = base + "/" + path
            else:
                full_url = base + path

            self.query_one("#api-url", Input).value = full_url

    async def send_request(self) -> None:
        method = self.query_one("#api-method", Select).value
        url = self.query_one("#api-url", Input).value
        body = self.query_one("#api-body", Input).value

        if not url:
            self.notify("URL required.", severity="error")
            return

        log = self.query_one("#api-response-log", RichLog)
        log.clear()
        log.write(f"Sending {method} {url}...")

        import asyncio
        # Run in thread
        result = await asyncio.to_thread(self.manager.execute_request, method, url, body=body)

        status = result['status_code']
        color = "green" if result['success'] else "red"

        log.write(f"Status: [{color}]{status}[/{color}]")
        log.write("[bold]Headers:[/bold]")
        for k, v in result['headers'].items():
            log.write(f"  {k}: {v}")

        log.write("\n[bold]Body:[/bold]")
        try:
            # Attempt to highlight JSON
            if result['body'].strip().startswith("{") or result['body'].strip().startswith("["):
                log.write(Syntax(result['body'], "json", theme="monokai"))
            else:
                log.write(result['body'])
        except Exception:
            log.write(result['body'])


class PlanTab(Container):
    """Tab for Project Planning (Spec & Feature List)."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.feature_list_path = project_dir / "feature_list.json"
        self.spec_path = project_dir / "app_spec.txt"

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: App Spec
            with Vertical(id="plan-spec-container", classes="stat-box"):
                yield Label("[bold]Application Specification[/bold]")
                yield TextArea(language="text", id="spec-editor")
                with Horizontal():
                    yield Button("Save Spec", id="btn-save-spec", variant="primary")
                    yield Button("Generate Plan", id="btn-generate-plan", variant="warning")

            # Right Pane: Feature List
            with Vertical(id="plan-features-container", classes="stat-box"):
                yield Label("[bold]Feature Plan[/bold]")
                yield DataTable(id="features-table")

                with Horizontal():
                    yield Input(placeholder="Feature Name...", id="feature-name-input")
                    yield Button("Add Feature", id="btn-add-feature", variant="success")

                yield Button("Refresh", id="btn-refresh-plan", variant="default")
                yield Label("", id="plan-status")

    def on_mount(self) -> None:
        table = self.query_one("#features-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Name", "Status", "Description")
        self.load_data()

    def load_data(self) -> None:
        # Load Spec
        if self.spec_path.exists():
            try:
                content = self.spec_path.read_text()
                self.query_one("#spec-editor", TextArea).text = content
            except Exception as e:
                self.notify(f"Error reading spec: {e}", severity="error")
        else:
            self.query_one("#spec-editor", TextArea).text = ""

        # Load Features
        self.load_features()

    def load_features(self) -> None:
        table = self.query_one("#features-table", DataTable)
        table.clear()

        if self.feature_list_path.exists():
            try:
                features = json.loads(self.feature_list_path.read_text())
                for f in features:
                    name = f.get("name", "Unknown")
                    status = f.get("status", "pending")
                    desc = f.get("description", "")

                    status_fmt = f"[green]{status}[/green]" if status == "completed" else status
                    table.add_row(name, status_fmt, desc)
            except Exception as e:
                self.notify(f"Error reading feature list: {e}", severity="error")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-save-spec":
            self.save_spec()
        elif event.button.id == "btn-generate-plan":
            await self.generate_plan()
        elif event.button.id == "btn-add-feature":
            self.add_feature()
        elif event.button.id == "btn-refresh-plan":
            self.load_data()
            self.notify("Plan refreshed.")

    def save_spec(self) -> None:
        content = self.query_one("#spec-editor", TextArea).text
        try:
            self.spec_path.write_text(content)
            self.notify("Application spec saved.")
        except Exception as e:
            self.notify(f"Error saving spec: {e}", severity="error")

    async def generate_plan(self) -> None:
        self.save_spec() # Save first
        self.notify("Generating plan... (this may take a minute)")
        self.query_one("#plan-status", Label).update("Generating Plan with AI...")

        # Disable button
        self.query_one("#btn-generate-plan", Button).disabled = True

        import asyncio

        try:
            # We assume default agent 'gemini' for now, or could add a selector
            success = await run_plan_logic(
                self.project_dir,
                spec_file=self.spec_path,
                agent_type="gemini"
            )

            if success:
                self.notify("Plan generated successfully!")
                self.query_one("#plan-status", Label).update("Plan Generated.")
                self.load_features()
            else:
                self.notify("Plan generation failed.", severity="error")
                self.query_one("#plan-status", Label).update("Generation Failed.")

        except Exception as e:
            self.notify(f"Error generating plan: {e}", severity="error")
            self.query_one("#plan-status", Label).update("Error.")
        finally:
            self.query_one("#btn-generate-plan", Button).disabled = False

    def add_feature(self) -> None:
        inp = self.query_one("#feature-name-input", Input)
        name = inp.value
        if not name:
            self.notify("Feature name required.", severity="error")
            return

        features = []
        if self.feature_list_path.exists():
            try:
                features = json.loads(self.feature_list_path.read_text())
            except Exception:
                pass

        # Check duplicate
        if any(f.get("name") == name for f in features):
            self.notify("Feature already exists.", severity="warning")
            return

        features.append({
            "name": name,
            "description": "Added via TUI",
            "status": "pending"
        })

        try:
            self.feature_list_path.write_text(json.dumps(features, indent=2))
            self.notify(f"Feature '{name}' added.")
            inp.value = ""
            self.load_features()
        except Exception as e:
            self.notify(f"Error saving feature list: {e}", severity="error")


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
        with TabbedContent(id="main-tabs"):
            with TabPane("Dashboard", id="tab-dashboard"):
                yield DashboardTab(self.project_dir)
            with TabPane("Plan", id="tab-plan"):
                yield PlanTab(self.project_dir)
            with TabPane("Interact", id="tab-interact"):
                yield InteractTab(self.project_dir)
            with TabPane("Recipes", id="tab-recipes"):
                yield RecipesTab(self.project_dir)
            with TabPane("Search", id="tab-search"):
                yield SearchTab(self.project_dir)
            with TabPane("Tasks", id="tab-tasks"):
                yield TasksTab(self.project_dir)
            with TabPane("Git", id="tab-git"):
                yield GitTab(self.project_dir)
            with TabPane("Worktrees", id="tab-worktrees"):
                yield WorktreesTab(self.project_dir)
            with TabPane("Dependencies", id="tab-deps"):
                yield DependenciesTab(self.project_dir)
            with TabPane("Analytics", id="tab-analytics"):
                yield AnalyticsTab(self.project_dir)
            with TabPane("Knowledge", id="tab-knowledge"):
                yield KnowledgeTab(self.project_dir)
            with TabPane("Explorer", id="tab-explorer"):
                yield FileExplorerTab(self.project_dir)
            with TabPane("Code Map", id="tab-codemap"):
                yield CodeMapTab(self.project_dir)
            with TabPane("Profiler", id="tab-profile"):
                yield ProfileTab(self.project_dir)
            with TabPane("Sessions", id="tab-sessions"):
                yield SessionTab(self.project_dir)
            with TabPane("Logs", id="tab-logs"):
                yield LogsTab()
            with TabPane("Database", id="tab-database"):
                yield DatabaseTab(self.project_dir)
            with TabPane("Secrets", id="tab-secrets"):
                yield SecretsTab(self.project_dir)
            with TabPane("API Lab", id="tab-api-lab"):
                yield ApiLabTab(self.project_dir)
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
