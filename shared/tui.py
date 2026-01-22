import sys
import io
import contextlib
import os
import shlex
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, RichLog, DirectoryTree, TabbedContent, TabPane, Button, Label, Input, DataTable, Select, Markdown, ListView, ListItem
from textual.containers import Container, Horizontal, VerticalScroll, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.binding import Binding
from textual import on

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

# Helper to get Git info safely
def get_git_info(project_dir: Path) -> dict[str, str]:
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
        self.tasks_cache: list[Task] = []

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

class ProfileTab(Container):
    """Tab for performance profiling."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = OptimizationManager(project_dir)
        self.stats_file: Path | None = None

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


from typing import Any

def collect_analytics_data(project_dir: Path) -> dict[str, Any]:
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

    def _update_ui(self, data: dict[str, Any]) -> None:
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
            with TabPane("Tasks", id="tab-tasks"):
                yield TasksTab(self.project_dir)
            with TabPane("Dependencies", id="tab-deps"):
                yield DependenciesTab(self.project_dir)
            with TabPane("Analytics", id="tab-analytics"):
                yield AnalyticsTab(self.project_dir)
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
