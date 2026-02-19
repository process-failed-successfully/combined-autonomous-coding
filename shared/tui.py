import contextlib
import io
import os
import shlex
import sys
from pathlib import Path

import yaml
from rich.syntax import Syntax
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import (Button, Checkbox, DataTable, DirectoryTree,
                             Footer, Header, Input, Label, ListItem, ListView,
                             Markdown, RichLog, Select, TabbedContent, TabPane,
                             TextArea, Tree)

from shared.api_collections import ApiCollectionManager
from shared.api_lab import ApiLabManager
from shared.ask import run_ask_logic
from shared.charts import draw_ascii_bar_chart
from shared.cli_utils import get_workflow_stage
from shared.code_review import run_code_review_logic
from shared.config_loader import load_config_from_file
from shared.cost import CostCalculator
from shared.database import init_db
from shared.debt import DebtCollector
from shared.docstring import DocstringManager
from shared.health import HealthCalculator
from shared.knowledge import KnowledgeManager
from shared.link_checker import LinkChecker
from shared.map import scan_project
from shared.openapi import OpenAPIGenerator
from shared.optimize import OptimizationManager
from shared.plan import run_plan_logic
from shared.playground import PlaygroundManager
from shared.plugin_manager import PluginManager
from shared.prompt_lab import PromptLabManager
from shared.recipe_learner import RecipeLearner
from shared.recipes import RecipeManager
from shared.refactor import RefactorManager
from shared.release import (determine_next_version, generate_changelog,
                            get_commits_since_tag, get_latest_tag,
                            parse_current_version, perform_release)
from shared.replace import replace_in_codebase
from shared.scaffold import ScaffoldManager
from shared.search import search_codebase
from shared.secrets import SecretsManager
from shared.security import SecurityAuditor
from shared.task_manager import Task, TaskManager
from shared.timeline import TimelineCollector, TimelineRenderer
from shared.troubleshoot import TroubleshootManager
from shared.tui_adr import ADRTab
from shared.tui_bisect import BisectTab
from shared.tui_chaos import ChaosTab
from shared.tui_command_palette import AgentCommandPalette, PaletteCommand
from shared.tui_conflict import ConflictTab
from shared.tui_cron import CronLabTab
from shared.tui_csv import CsvLabTab
from shared.tui_database import DatabaseTab
from shared.tui_database_diagram import DatabaseDiagramTab
from shared.tui_datalab import DataLabTab
from shared.tui_dependencies import DependenciesTab
from shared.tui_devtools import DevToolsTab
from shared.tui_diff_lab import DiffLabTab
from shared.tui_disk_usage import DiskUsageTab
from shared.tui_docker import DockerTab
from shared.tui_env import EnvTab
from shared.tui_explorer import FileExplorerTab
from shared.tui_frontend import FrontendTab
from shared.tui_gantt import GanttTab
from shared.tui_git import GitTab
from shared.tui_guardrails import GuardrailsTab
from shared.tui_hex import HexTab
from shared.tui_i18n import I18nTab
from shared.tui_ide_config import IdeConfigTab
from shared.tui_image import ImageLabTab
from shared.tui_impact import ImpactTab
from shared.tui_json import JsonLabTab
from shared.tui_jwt import JwtLabTab
from shared.tui_k8s import K8sTab
from shared.tui_kanban import KanbanBoard
from shared.tui_log_explorer import LogExplorerTab
from shared.tui_logic import LogicLabTab
from shared.tui_markdown import MarkdownLabTab
from shared.tui_math import MathLabTab
from shared.tui_net_diag import NetDiagTab
from shared.tui_network import NetworkTab
from shared.tui_presentation import PresentationTab
from shared.tui_proc import ProcLabTab
from shared.tui_pull_requests import PullRequestsTab
from shared.tui_quiz import QuizTab
from shared.tui_regex import RegexLabTab
from shared.tui_research import ResearchTab
from shared.tui_sanitizer import SanitizerTab
from shared.tui_scheduler import SchedulerTab
from shared.tui_security import SecurityTab
from shared.tui_semver import SemVerTab
from shared.tui_sentinel import SentinelTab
from shared.tui_services import ServicesTab
from shared.tui_snippets import SnippetsTab
from shared.tui_standup import StandupTab
from shared.tui_system_monitor import SystemMonitorTab
from shared.tui_terminal import TerminalTab
from shared.tui_terraform import TerraformTab
from shared.tui_time import TimeLabTab
from shared.tui_yaml import YamlLabTab
from shared.work_session import WorkSessionManager
from shared.worktree import WorktreeManager


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

class ScaffoldTab(Container):
    """Tab for project scaffolding (Templates & AI)."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = ScaffoldManager(project_dir)
        self.ai_plan = {}

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: Templates
            with Vertical(id="scaffold-list-container", classes="stat-box"):
                yield Label("[bold]Templates[/bold]")
                yield ListView(id="scaffold-template-list")
                yield Button("Refresh", id="btn-scaffold-refresh", variant="default")

            # Center Pane: Configuration
            with Vertical(id="scaffold-config-container"):
                yield Label("[bold]Configuration[/bold]")

                with Vertical(classes="stat-box"):
                    yield Label("Description / Custom Instructions:")
                    yield TextArea(id="scaffold-description", disabled=True)

                    with Horizontal():
                        yield Select.from_values(["gemini", "cursor", "local"], id="scaffold-agent", value="gemini")
                        yield Button("Generate Preview (AI)", id="btn-scaffold-preview", variant="warning", disabled=True)

                yield Button("Create Project", id="btn-scaffold-create", variant="primary", disabled=True)

            # Right Pane: Preview
            with Vertical(id="scaffold-preview-container", classes="stat-box"):
                yield Label("[bold]File Preview[/bold]")
                yield RichLog(id="scaffold-preview-log", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        self.load_templates()

    def load_templates(self) -> None:
        list_view = self.query_one("#scaffold-template-list", ListView)
        list_view.clear()

        # Add "AI Custom" option first
        ai_item = ListItem(Label("[bold magenta]✨ AI Custom Scaffold[/bold magenta]"))
        ai_item.template_name = "ai_custom"
        list_view.append(ai_item)

        templates = self.manager.list_templates()
        for name, desc in templates.items():
            item = ListItem(Label(f"[bold]{name}[/bold]\n[dim]{desc}[/dim]"))
            item.template_name = name
            list_view.append(item)

    @on(ListView.Selected, "#scaffold-template-list")
    def on_template_selected(self, event: ListView.Selected) -> None:
        if not hasattr(event.item, "template_name"):
            return

        name = event.item.template_name
        desc_area = self.query_one("#scaffold-description", TextArea)
        preview_btn = self.query_one("#btn-scaffold-preview", Button)
        create_btn = self.query_one("#btn-scaffold-create", Button)
        preview_log = self.query_one("#scaffold-preview-log", RichLog)

        preview_log.clear()
        self.ai_plan = {}

        if name == "ai_custom":
            desc_area.disabled = False
            desc_area.text = ""
            desc_area.focus()
            preview_btn.disabled = False
            create_btn.disabled = True # Wait for preview
            preview_log.write("Enter a description and click 'Generate Preview'.")
        else:
            desc_area.disabled = True
            desc_area.text = f"Selected Template: {name}"
            preview_btn.disabled = True
            create_btn.disabled = False
            preview_log.write(f"Ready to scaffold '{name}'.")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-scaffold-refresh":
            self.load_templates()
        elif event.button.id == "btn-scaffold-preview":
            await self.generate_preview()
        elif event.button.id == "btn-scaffold-create":
            await self.create_project()

    async def generate_preview(self) -> None:
        desc = self.query_one("#scaffold-description", TextArea).text
        if not desc:
            self.notify("Description required.", severity="error")
            return

        agent_type = self.query_one("#scaffold-agent", Select).value or "gemini"
        log = self.query_one("#scaffold-preview-log", RichLog)

        log.clear()
        log.write(f"Generating plan with {agent_type}...")
        self.notify("Generating plan...", severity="information")

        # Run in thread
        self.ai_plan = await self.manager.generate_ai_scaffold(desc, agent_type=agent_type)

        log.clear()
        if self.ai_plan:
            log.write("[bold green]Proposed File Structure:[/bold green]")
            for path in sorted(self.ai_plan.keys()):
                log.write(f"📄 {path}")

            self.query_one("#btn-scaffold-create").disabled = False
            self.notify("Preview generated.")
        else:
            log.write("[bold red]Failed to generate plan.[/bold red]")
            self.notify("Generation failed.", severity="error")

    async def create_project(self) -> None:
        list_view = self.query_one("#scaffold-template-list", ListView)
        if list_view.index is None:
            return

        item = list_view.children[list_view.index]
        name = item.template_name

        self.notify("Creating project...")
        success = False

        if name == "ai_custom":
            if not self.ai_plan:
                self.notify("No plan generated.", severity="error")
                return
            success = self.manager.create_from_plan(self.ai_plan)
        else:
            success = self.manager.scaffold(name)

        if success:
            self.notify("Project created successfully!", severity="information")
            self.query_one("#scaffold-preview-log", RichLog).write("\n[bold green]Done![/bold green]")
        else:
            self.notify("Failed to create project.", severity="error")


class PlanTab(Container):
    """Tab for planning the project (spec -> plan)."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Project Plan Manager[/bold]", classes="welcome-text")

            with Horizontal(classes="stat-box"):
                yield Button("Save Spec", id="btn-save-spec", variant="success")
                yield Button("Generate Plan (AI)", id="btn-generate-plan", variant="primary")
                yield Button("Save Plan", id="btn-save-plan", variant="success")
                yield Select.from_values(["gemini", "cursor", "local"], id="plan-agent-select", value="gemini")

            with Horizontal():
                # Spec Pane
                with Vertical(classes="stat-box", id="spec-pane"):
                    yield Label("[bold]Application Spec (app_spec.txt)[/bold]")
                    yield TextArea("", language="markdown", id="spec-editor")

                # Plan Pane
                with Vertical(classes="stat-box", id="plan-pane"):
                    yield Label("[bold]Feature List (feature_list.json)[/bold]")
                    yield TextArea("", language="json", id="plan-editor")

    def on_mount(self) -> None:
        self.load_files()

    def load_files(self) -> None:
        # Load Spec
        spec_path = self.project_dir / "app_spec.txt"
        spec_editor = self.query_one("#spec-editor", TextArea)
        if spec_path.exists():
            spec_editor.text = spec_path.read_text(encoding="utf-8", errors="replace")
        else:
            spec_editor.text = "# Application Specification\n\nDescribe your app here..."

        # Load Plan
        plan_path = self.project_dir / "feature_list.json"
        plan_editor = self.query_one("#plan-editor", TextArea)
        if plan_path.exists():
            plan_editor.text = plan_path.read_text(encoding="utf-8", errors="replace")
        else:
            plan_editor.text = "[]"

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-save-spec":
            self.save_spec()
        elif event.button.id == "btn-save-plan":
            self.save_plan()
        elif event.button.id == "btn-generate-plan":
            await self.generate_plan()

    def save_spec(self) -> None:
        content = self.query_one("#spec-editor", TextArea).text
        path = self.project_dir / "app_spec.txt"
        try:
            path.write_text(content, encoding="utf-8")
            self.notify("Spec saved.")
        except Exception as e:
            self.notify(f"Error saving spec: {e}", severity="error")

    def save_plan(self) -> None:
        content = self.query_one("#plan-editor", TextArea).text
        path = self.project_dir / "feature_list.json"
        try:
            path.write_text(content, encoding="utf-8")
            self.notify("Plan saved.")
        except Exception as e:
            self.notify(f"Error saving plan: {e}", severity="error")

    async def generate_plan(self) -> None:
        # Save spec first
        self.save_spec()

        agent_type = self.query_one("#plan-agent-select", Select).value or "gemini"

        self.notify(f"Generating plan with {agent_type}...", severity="information", timeout=5)

        # Call logic
        try:
            success, message = await run_plan_logic(
                self.project_dir,
                agent_type=agent_type,
                capture_output=True
            )

            if success:
                self.notify("Plan generated successfully.")
                self.load_files() # Reload to show new plan
            else:
                self.notify(f"Plan generation failed: {message}", severity="error", timeout=10)
        except Exception as e:
             self.notify(f"Critical Error: {e}", severity="error")


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

class TimelineTab(Container):
    """Tab for viewing the project timeline."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.collector = TimelineCollector(project_dir)
        self.renderer = TimelineRenderer()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Project Timeline[/bold]", classes="welcome-text")

            with Horizontal(classes="stat-box"):
                yield Button("Refresh", id="btn-timeline-refresh", variant="primary")
                yield Button("Export HTML", id="btn-timeline-html", variant="success")

            yield RichLog(id="timeline-log", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        self.load_timeline()

    def load_timeline(self) -> None:
        log_view = self.query_one("#timeline-log", RichLog)
        log_view.clear()

        events = self.collector.get_timeline(limit=50)

        if not events:
            log_view.write("No events found.")
            return

        # Use the Rich Table object directly
        table = self.renderer.get_rich_table(events)
        log_view.write(table)

    @on(Button.Pressed, "#btn-timeline-refresh")
    def on_refresh(self) -> None:
        self.load_timeline()
        self.notify("Timeline refreshed.")

    @on(Button.Pressed, "#btn-timeline-html")
    def on_export_html(self) -> None:
        events = self.collector.get_timeline(limit=100)
        html_content = self.renderer.render_html(events)

        output_path = self.project_dir / "timeline.html"
        try:
            output_path.write_text(html_content, encoding="utf-8")
            self.notify(f"Timeline exported to {output_path.name}")
        except Exception as e:
            self.notify(f"Error exporting timeline: {e}", severity="error")



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

            with TabbedContent():
                with TabPane("List View"):
                    yield DataTable(id="tasks-table")
                with TabPane("Kanban View"):
                    yield KanbanBoard(id="kanban-board")

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

            # Update Kanban
            try:
                kanban = self.query_one("#kanban-board", KanbanBoard)
                kanban.load_tasks(tasks)
            except Exception:
                pass

            self.notify(f"Loaded {len(tasks)} tasks.")
        except Exception as e:
            self.notify(f"Error fetching tasks: {e}", severity="error")

    @on(KanbanBoard.StatusUpdate)
    def on_status_update(self, event: KanbanBoard.StatusUpdate) -> None:
        self.notify(f"Updating task {event.task_id} to {event.new_status}...")

        # Run in thread to avoid blocking UI
        import asyncio
        asyncio.create_task(self._async_update_status(event.task_id, event.new_status))

    async def _async_update_status(self, task_id: str, new_status: str) -> None:
        import asyncio
        success = await asyncio.to_thread(self.task_manager.update_task_status, task_id, new_status)

        if success:
            self.notify(f"Task {task_id} updated.")
            self.load_tasks()
        else:
            self.notify(f"Failed to update task {task_id}.", severity="error")

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




class SearchTab(Container):
    """Tab for searching code (Grep)."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.replace_preview_data = {}

    def compose(self) -> ComposeResult:
        with Horizontal(classes="stat-box"):
            yield Input(placeholder="Search pattern...", id="search-input")
            yield Button("Search", id="btn-search", variant="primary")

        with Horizontal(classes="stat-box"):
            yield Input(placeholder="Replacement...", id="replace-input")
            yield Button("Preview Replace", id="btn-preview-replace", variant="warning")
            yield Button("Apply Replace", id="btn-apply-replace", variant="error", disabled=True)

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
        elif event.button.id == "btn-preview-replace":
            await self.preview_replace()
        elif event.button.id == "btn-apply-replace":
            await self.apply_replace()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "search-input":
            await self.perform_search()

    async def preview_replace(self) -> None:
        pattern = self.query_one("#search-input", Input).value
        replacement = self.query_one("#replace-input", Input).value

        if not pattern:
            self.notify("Search pattern required.", severity="error")
            return

        case_sensitive = self.query_one("#chk-case", Checkbox).value
        is_regex = self.query_one("#chk-regex", Checkbox).value
        file_pattern = self.query_one("#file-pattern-input", Input).value

        log = self.query_one("#search-preview", RichLog)
        log.clear()
        self.notify("Generating preview...")

        import asyncio
        try:
            # Run in thread
            stats = await asyncio.to_thread(
                replace_in_codebase,
                self.project_dir,
                pattern,
                replacement,
                file_pattern=file_pattern if file_pattern else None,
                case_sensitive=case_sensitive,
                is_regex=is_regex,
                dry_run=True
            )

            self.replace_preview_data = stats

            log.write(f"[bold]Preview Replace: {pattern} -> {replacement}[/bold]")
            log.write(f"Files matched: {stats['files_matched']}")
            log.write(f"Files changed: {stats['files_changed']}")
            log.write(f"Replacements: {stats['replacements_count']}")

            if stats['files_changed'] > 0:
                self.query_one("#btn-apply-replace").disabled = False
                log.write("\n[bold]Diffs:[/bold]")
                for file, diff in stats['diffs'].items():
                    log.write(f"\n[bold]{file}[/bold]")
                    log.write(Syntax(diff, "diff", theme="monokai"))
            else:
                self.query_one("#btn-apply-replace").disabled = True
                log.write("\nNo changes detected.")

        except Exception as e:
            self.notify(f"Error: {e}", severity="error")
            log.write(f"[red]Error: {e}[/red]")

    async def apply_replace(self) -> None:
        pattern = self.query_one("#search-input", Input).value
        replacement = self.query_one("#replace-input", Input).value

        # Re-fetch params to be safe
        case_sensitive = self.query_one("#chk-case", Checkbox).value
        is_regex = self.query_one("#chk-regex", Checkbox).value
        file_pattern = self.query_one("#file-pattern-input", Input).value

        self.notify("Applying replacements...")

        import asyncio
        try:
            stats = await asyncio.to_thread(
                replace_in_codebase,
                self.project_dir,
                pattern,
                replacement,
                file_pattern=file_pattern if file_pattern else None,
                case_sensitive=case_sensitive,
                is_regex=is_regex,
                dry_run=False
            )

            self.notify(f"Replaced {stats['replacements_count']} occurrences in {stats['files_changed']} files.")
            self.query_one("#btn-apply-replace").disabled = True

            # Refresh search results
            await self.perform_search()

        except Exception as e:
            self.notify(f"Error applying replace: {e}", severity="error")

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

                with Horizontal():
                    yield Button("Create Manual", id="btn-recipe-create", variant="primary")
                    yield Button("Learn from Last Run", id="btn-recipe-learn", variant="warning")

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

        elif event.button.id == "btn-recipe-learn":
            await self.learn_recipe()

        elif event.button.id == "btn-recipe-run":
            await self.run_recipe()

        elif event.button.id == "btn-recipe-delete":
            await self.delete_recipe()

    async def learn_recipe(self) -> None:
        name_inp = self.query_one("#recipe-new-name", Input)
        name = name_inp.value

        if not name:
            self.notify("Name required.", severity="error")
            return

        self.notify(f"Learning recipe '{name}' from last run...", severity="information")
        log = self.query_one("#recipe-log", RichLog)
        log.write(f"\n[bold yellow]Learning recipe '{name}'...[/bold yellow]")

        learner = RecipeLearner(self.project_dir)
        output_capture = io.StringIO()
        success = False

        try:
            with contextlib.redirect_stdout(output_capture):
                # Pass None for run_id to use latest
                success = await learner.learn_from_run(None, name)
        except Exception as e:
            output_capture.write(f"Error: {e}")

        output = output_capture.getvalue()
        log.write(output)

        if success:
            self.notify(f"Recipe '{name}' learned.")
            name_inp.value = ""
            self.load_recipes()
        else:
            self.notify("Failed to learn recipe.", severity="error")

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


class TUIStream:
    """Helper to redirect stdout to a RichLog widget in a thread-safe way."""
    def __init__(self, log_widget, app):
        self.log = log_widget
        self.app = app

    def write(self, text):
        if text.strip():
            # Use call_from_thread because this will be called from a background thread
            # Use rstrip() to remove trailing newline from print(), but keep leading indentation
            self.app.call_from_thread(self.log.write, text.rstrip())

    def flush(self):
        pass

class ApiLabTab(Container):
    """Tab for API experimentation and Collections."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = ApiLabManager(project_dir)
        self.collection_manager = ApiCollectionManager(project_dir)
        self.selected_endpoint = None
        self.selected_saved_request = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: Tabbed content for Spec vs Saved
            with Vertical(id="api-list-container", classes="stat-box"):
                with TabbedContent():
                    with TabPane("Spec"):
                        yield Label("[bold]Endpoints[/bold]")
                        yield ListView(id="api-endpoint-list")
                        with Horizontal():
                            yield Button("Load Spec", id="btn-api-load", variant="primary")
                            yield Button("Generate", id="btn-api-generate", variant="warning")

                    with TabPane("Saved"):
                        yield Label("[bold]Collections[/bold]")
                        yield ListView(id="api-collection-list")
                        yield Button("Delete Saved", id="btn-api-delete-saved", variant="error", disabled=True)

            # Right Pane: Request/Response & Fuzzer
            with Vertical(id="api-details-container"):
                with TabbedContent():
                    with TabPane("Request"):
                        yield Label("[bold]Request Builder[/bold]")

                        with Vertical(classes="stat-box"):
                            yield Input(placeholder="Request Name (optional for saving)...", id="api-req-name")
                            # Request Line
                            with Horizontal():
                                yield Select.from_values(["GET", "POST", "PUT", "DELETE", "PATCH"], id="api-method", value="GET")
                                yield Input(placeholder="URL...", id="api-url")

                            with Horizontal():
                                yield Button("Send", id="btn-api-send", variant="success")
                                yield Button("Save", id="btn-api-save", variant="primary")

                        # Body
                        with Vertical(classes="stat-box"):
                            yield Label("Request Body (JSON):")
                            yield Input(placeholder="{ ... }", id="api-body")

                        # Response
                        yield Label("[bold]Response[/bold]")
                        yield RichLog(id="api-response-log", wrap=True, highlight=True, markup=True)

                    with TabPane("Fuzzer"):
                        yield Label("[bold]Interactive API Fuzzer[/bold]", classes="welcome-text")
                        with Container(classes="stat-box"):
                            yield Label("Target Endpoint:", classes="label")
                            yield Label("None", id="lbl-fuzz-target", classes="value")
                            yield Button("Start Fuzzing", id="btn-api-fuzz", variant="warning")

                        yield Label("[bold]Fuzzing Log[/bold]")
                        yield RichLog(id="api-fuzzer-log", wrap=True, highlight=True, markup=True)

                    with TabPane("Load Test"):
                        yield Label("[bold]API Load Tester[/bold]", classes="welcome-text")

                        with Vertical(classes="stat-box"):
                            with Horizontal():
                                yield Select.from_values(["GET", "POST", "PUT", "DELETE", "PATCH"], id="api-load-method", value="GET")
                                yield Input(placeholder="URL...", id="api-load-url")

                            with Horizontal():
                                yield Input(placeholder="Users (default 10)", id="api-load-users", type="integer")
                                yield Input(placeholder="Duration (s) (default 5)", id="api-load-duration", type="integer")

                            yield Label("Request Body (JSON):")
                            yield TextArea(id="api-load-body", language="json")

                            yield Button("Start Load Test", id="btn-api-load-start", variant="warning")

                        yield Label("[bold]Test Results[/bold]")
                        yield RichLog(id="api-load-log", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        self.load_spec()
        self.load_collections()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-api-load":
            self.load_spec(force_reload=True)
        elif event.button.id == "btn-api-generate":
            await self.generate_spec()
        elif event.button.id == "btn-api-send":
            await self.send_request()
        elif event.button.id == "btn-api-save":
            self.save_current_request()
        elif event.button.id == "btn-api-delete-saved":
            self.delete_saved_request()
        elif event.button.id == "btn-api-fuzz":
            await self.run_fuzzer()
        elif event.button.id == "btn-api-load-start":
            await self.run_load_test()

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

    def load_collections(self) -> None:
        list_view = self.query_one("#api-collection-list", ListView)
        list_view.clear()

        requests = self.collection_manager.list_requests()
        for req in requests:
            method = req['method']
            name = req.get('name', 'Untitled')
            # Color code method
            if method == "GET": method_fmt = f"[blue]{method}[/blue]"
            elif method == "POST": method_fmt = f"[green]{method}[/green]"
            elif method == "DELETE": method_fmt = f"[red]{method}[/red]"
            else: method_fmt = f"[yellow]{method}[/yellow]"

            label = f"{method_fmt} {name}"
            item = ListItem(Label(label, markup=True))
            item.request_data = req
            list_view.append(item)

    async def generate_spec(self) -> None:
        self.notify("Generating OpenAPI spec... (this takes time)")
        from shared.openapi import OpenAPIGenerator

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
            self.query_one("#api-req-name", Input).value = "" # Clear name for fresh endpoint

            # Pre-populate Load Test fields as well
            try:
                self.query_one("#api-load-method", Select).value = data['method']
                self.query_one("#api-load-url", Input).value = full_url
            except Exception:
                pass

            # Update Fuzz Target Label
            try:
                self.query_one("#lbl-fuzz-target", Label).update(f"[{data['method']}] {full_url}")
            except Exception:
                pass

    @on(ListView.Selected, "#api-collection-list")
    def on_saved_request_selected(self, event: ListView.Selected) -> None:
        if hasattr(event.item, "request_data"):
            data = event.item.request_data
            self.selected_saved_request = data.get("id")

            self.query_one("#api-method", Select).value = data.get('method', 'GET')
            self.query_one("#api-url", Input).value = data.get('url', '')
            self.query_one("#api-body", Input).value = data.get('body', '')
            self.query_one("#api-req-name", Input).value = data.get('name', '')

            # Also populate Load Test fields
            try:
                self.query_one("#api-load-method", Select).value = data.get('method', 'GET')
                self.query_one("#api-load-url", Input).value = data.get('url', '')
                self.query_one("#api-load-body", TextArea).text = data.get('body', '') # Note: TextArea uses .text not .value
            except Exception:
                pass

            self.query_one("#btn-api-delete-saved").disabled = False
            self.notify(f"Loaded '{data.get('name')}'")

    def save_current_request(self) -> None:
        name = self.query_one("#api-req-name", Input).value
        method = self.query_one("#api-method", Select).value
        url = self.query_one("#api-url", Input).value
        body = self.query_one("#api-body", Input).value

        if not name:
            self.notify("Please enter a Request Name to save.", severity="error")
            self.query_one("#api-req-name", Input).focus()
            return

        if not url:
            self.notify("URL required.", severity="error")
            return

        # Headers support is minimal in UI for now, defaulting to empty or json if body present
        headers = {}
        if body:
            headers["Content-Type"] = "application/json"

        self.collection_manager.save_request(name, method, url, headers, body)
        self.notify(f"Request '{name}' saved.")
        self.load_collections()

    def delete_saved_request(self) -> None:
        if not self.selected_saved_request:
            return

        if self.collection_manager.delete_request(self.selected_saved_request):
            self.notify("Request deleted.")
            self.selected_saved_request = None
            self.query_one("#btn-api-delete-saved").disabled = True
            self.load_collections()
        else:
            self.notify("Failed to delete request.", severity="error")

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

    async def run_fuzzer(self) -> None:
        method = self.query_one("#api-method", Select).value
        url = self.query_one("#api-url", Input).value

        if not url:
            self.notify("URL required.", severity="error")
            return

        log = self.query_one("#api-fuzzer-log", RichLog)
        log.clear()
        log.write(f"[bold]Fuzzing {method} {url}...[/bold]")
        self.notify("Fuzzing started...")
        self.query_one("#btn-api-fuzz").disabled = True

        import asyncio
        import contextlib

        # Create TUIStream
        stream = TUIStream(log, self.app)

        def do_fuzz():
            with contextlib.redirect_stdout(stream):
                return self.manager.fuzz_endpoint(method, url)

        try:
            results = await asyncio.to_thread(do_fuzz)

            crashes = [r for r in results if r['crash']]
            log.write(f"\n[bold]Fuzzing Complete.[/bold]")
            log.write(f"Total Requests: {len(results)}")
            log.write(f"Crashes: {len(crashes)}")

            if crashes:
                log.write("[bold red]CRASHES DETECTED:[/bold red]")
                for c in crashes:
                    log.write(f"  Payload: {c['payload']} -> Status: {c['status']}")
            else:
                log.write("[bold green]No crashes detected.[/bold green]")

            self.notify("Fuzzing complete.")

        except Exception as e:
            log.write(f"[bold red]Fuzzing Error:[/bold red] {e}")
            self.notify(f"Error: {e}", severity="error")
        finally:
            self.query_one("#btn-api-fuzz").disabled = False

    async def run_load_test(self) -> None:
        method = self.query_one("#api-load-method", Select).value
        url = self.query_one("#api-load-url", Input).value

        users_str = self.query_one("#api-load-users", Input).value
        users = int(users_str) if users_str else 10

        duration_str = self.query_one("#api-load-duration", Input).value
        duration = int(duration_str) if duration_str else 5

        body = self.query_one("#api-load-body", TextArea).text

        if not url:
            self.notify("URL required.", severity="error")
            return

        log = self.query_one("#api-load-log", RichLog)
        log.clear()
        log.write(f"[bold]Starting Load Test: {method} {url}[/bold]")
        log.write(f"Users: {users} | Duration: {duration}s")
        self.notify("Load testing started...")
        self.query_one("#btn-api-load-start").disabled = True

        import asyncio

        try:
            results = await asyncio.to_thread(
                self.manager.load_test_endpoint,
                method, url, users, duration, body
            )

            log.write("\n[bold green]Test Complete[/bold green]")
            log.write(f"Total Requests: {results['total_requests']}")
            log.write(f"RPS: {results['rps']:.2f}")
            log.write(f"Avg Latency: {results['avg_latency']:.2f} ms")
            log.write(f"P50 Latency: {results['p50_latency']:.2f} ms")
            log.write(f"P95 Latency: {results['p95_latency']:.2f} ms")
            log.write(f"P99 Latency: {results['p99_latency']:.2f} ms")

            if results['errors'] > 0:
                log.write(f"[bold red]Errors: {results['errors']}[/bold red]")
            else:
                log.write("Errors: 0")

            log.write("\n[bold]Status Codes:[/bold]")
            for code, count in results['status_codes'].items():
                color = "green" if 200 <= code < 300 else "red"
                log.write(f"  [{color}]{code}[/{color}]: {count}")

            self.notify("Load test finished.")

        except Exception as e:
            log.write(f"[bold red]Error:[/bold red] {e}")
            self.notify(f"Error: {e}", severity="error")
        finally:
            self.query_one("#btn-api-load-start").disabled = False


class PlaygroundTab(Container):
    """Tab for experimenting with code snippets."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = PlaygroundManager(project_dir)
        self.current_file = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: File List
            with Vertical(id="playground-list-container", classes="stat-box"):
                yield Label("[bold]Scripts[/bold]")
                yield ListView(id="playground-list")
                with Horizontal():
                    yield Input(placeholder="New script name...", id="playground-new-name")
                    yield Button("Create", id="btn-playground-create", variant="primary")
                yield Button("Refresh", id="btn-playground-refresh", variant="default")

            # Right Pane: Editor & Output
            with Vertical(id="playground-editor-container"):
                yield Label("[bold]Editor[/bold]")
                yield TextArea(id="playground-editor", language="python")

                with Horizontal(id="playground-actions"):
                    yield Button("Save", id="btn-playground-save", variant="success")
                    yield Button("Run", id="btn-playground-run", variant="warning")
                    yield Button("Delete", id="btn-playground-delete", variant="error")

                yield Label("[bold]Output[/bold]")
                yield RichLog(id="playground-output", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        self.load_files()

    def load_files(self) -> None:
        list_view = self.query_one("#playground-list", ListView)
        list_view.clear()

        files = self.manager.list_files()
        if not files:
            list_view.append(ListItem(Label("No scripts found")))
            return

        for f in files:
            list_view.append(ListItem(Label(f.name), name=f.name))

    @on(ListView.Selected, "#playground-list")
    def on_file_selected(self, event: ListView.Selected) -> None:
        # Get filename from ListItem name if possible, or Label
        # Textual ListItems don't inherently store data easily unless subclassed or monkey-patched.
        # But we set name=f.name in load_files.
        if event.item and event.item.name:
            self.load_file_content(event.item.name)

    def load_file_content(self, filename: str) -> None:
        self.current_file = filename
        editor = self.query_one("#playground-editor", TextArea)
        path = self.manager.playground_dir / filename

        try:
            content = path.read_text(encoding="utf-8")
            editor.text = content
            # Update header or notify
            self.notify(f"Loaded {filename}")
        except Exception as e:
            self.notify(f"Error loading file: {e}", severity="error")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-playground-refresh":
            self.load_files()
        elif event.button.id == "btn-playground-create":
            await self.create_file()
        elif event.button.id == "btn-playground-save":
            await self.save_file()
        elif event.button.id == "btn-playground-run":
            await self.run_file()
        elif event.button.id == "btn-playground-delete":
            await self.delete_file()

    async def create_file(self) -> None:
        inp = self.query_one("#playground-new-name", Input)
        name = inp.value
        if not name:
            self.notify("Name required.", severity="error")
            return

        try:
            path = self.manager.create(name)
            self.notify(f"Created {path.name}")
            inp.value = ""
            self.load_files()
            self.load_file_content(path.name)
        except Exception as e:
            self.notify(f"Error creating file: {e}", severity="error")

    async def save_file(self) -> None:
        if not self.current_file:
            self.notify("No file selected.", severity="warning")
            return

        editor = self.query_one("#playground-editor", TextArea)
        path = self.manager.playground_dir / self.current_file
        try:
            path.write_text(editor.text, encoding="utf-8")
            self.notify("File saved.")
        except Exception as e:
            self.notify(f"Error saving file: {e}", severity="error")

    async def run_file(self) -> None:
        if not self.current_file:
            self.notify("No file selected.", severity="warning")
            return

        # Auto-save before running
        await self.save_file()

        output_log = self.query_one("#playground-output", RichLog)
        output_log.clear()
        output_log.write(f"Running {self.current_file}...")

        import asyncio

        # Run in thread
        try:
            # We updated manager.run to return (success, output) when capture_output=True
            def run_in_thread():
                return self.manager.run(self.current_file, capture_output=True)

            success, output = await asyncio.to_thread(run_in_thread)

            if success:
                output_log.write("[bold green]Success[/bold green]")
            else:
                output_log.write("[bold red]Failed[/bold red]")

            output_log.write(output)

        except Exception as e:
            output_log.write(f"[bold red]Execution Error:[/bold red] {e}")

    async def delete_file(self) -> None:
        if not self.current_file:
            return

        try:
            if self.manager.delete(self.current_file):
                self.notify(f"Deleted {self.current_file}")
                self.current_file = None
                self.query_one("#playground-editor", TextArea).text = ""
                self.load_files()
            else:
                self.notify("File not found.", severity="error")
        except Exception as e:
            self.notify(f"Error deleting file: {e}", severity="error")


class CodeReviewTab(Container):
    """Tab for AI Code Review."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]AI Code Review[/bold]", classes="welcome-text")

            with Horizontal():
                # Left Pane: Controls & Files
                with Vertical(id="review-controls-container", classes="stat-box"):
                    yield Label("[bold]Modified Files[/bold]")
                    yield ListView(id="review-file-list")

                    with Horizontal():
                        yield Button("Refresh", id="btn-review-refresh", variant="default")
                        yield Select.from_values(["gemini", "cursor", "local"], id="review-agent-select", value="gemini")

                    yield Button("Review Selected", id="btn-review-selected", variant="primary")
                    yield Button("Review All (Diff)", id="btn-review-all", variant="warning")

                # Right Pane: Report
                with VerticalScroll(id="review-report-container"):
                    yield Label("[bold]Review Report[/bold]")
                    yield Markdown("", id="review-markdown")

    def on_mount(self) -> None:
        self.load_files()

    def load_files(self) -> None:
        list_view = self.query_one("#review-file-list", ListView)
        list_view.clear()

        # Get git status
        import subprocess
        try:
            res = subprocess.run(
                ["git", "-C", str(self.project_dir), "status", "--porcelain"],
                capture_output=True,
                text=True
            )
            if res.returncode != 0:
                list_view.append(ListItem(Label("Error getting git status")))
                return

            lines = res.stdout.strip().split('\n')
            if not lines or not lines[0]:
                list_view.append(ListItem(Label("No modified files")))
                return

            for line in lines:
                if not line.strip(): continue
                # format: XY path
                status = line[:2]
                path = line[3:]
                # We use Checkbox for selection
                cb = Checkbox(f"[{status}] {path}", value=True)
                cb.file_path = path
                list_view.append(ListItem(cb))

        except Exception as e:
            list_view.append(ListItem(Label(f"Error: {e}")))

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-review-refresh":
            self.load_files()
            self.notify("File list refreshed.")
        elif event.button.id == "btn-review-selected":
            await self.run_review(selected_only=True)
        elif event.button.id == "btn-review-all":
            await self.run_review(selected_only=False)

    async def run_review(self, selected_only: bool) -> None:
        agent_type = self.query_one("#review-agent-select", Select).value or "gemini"

        files_to_review = []
        if selected_only:
            list_view = self.query_one("#review-file-list", ListView)
            for item in list_view.children:
                cb = item.query_one(Checkbox)
                if cb and cb.value:
                    if hasattr(cb, "file_path"):
                        files_to_review.append(cb.file_path)

            if not files_to_review:
                self.notify("No files selected.", severity="warning")
                return

        self.notify(f"Starting review with {agent_type}...", severity="information")
        report_view = self.query_one("#review-markdown", Markdown)
        report_view.update("Running review... please wait.")

        # Run logic and capture output
        output_capture = io.StringIO()
        success = False

        try:
            with contextlib.redirect_stdout(output_capture):
                success = await run_code_review_logic(
                    project_dir=self.project_dir,
                    files=files_to_review if selected_only else None,
                    diff=not selected_only,
                    agent_type=agent_type,
                    verbose=False
                )
        except Exception as e:
            output_capture.write(f"\nError: {e}")

        result = output_capture.getvalue()
        report_view.update(result)

        if success:
            self.notify("Review complete.")
        else:
            self.notify("Review failed.", severity="error")


class ReleaseTab(Container):
    """Tab for managing releases."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.commits = []
        self.changelog = ""

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Release Manager[/bold]", classes="welcome-text")

            # Status Section
            with Container(classes="stat-box"):
                yield Label("[bold]Current Status[/bold]")
                yield Label("Loading...", id="release-status-lbl")

            # Action Section
            with Container(classes="stat-box"):
                yield Label("Next Version:")
                with Horizontal():
                    yield Input(placeholder="0.0.0", id="release-version-input")
                    yield Button("Generate Changelog", id="btn-release-gen", variant="primary")

            # Preview Section
            with VerticalScroll(id="release-preview-container"):
                yield Label("[bold]Changelog Preview[/bold]")
                yield TextArea(id="release-changelog-editor")

            # Execute Section
            with Horizontal(classes="stat-box"):
                yield Button("Perform Release", id="btn-release-exec", variant="success", disabled=True)
                yield Checkbox("Dry Run", id="chk-release-dry", value=False)
                yield Label("", id="release-result-lbl")

    def on_mount(self) -> None:
        self.load_status()

    def load_status(self) -> None:
        tag = get_latest_tag(self.project_dir)
        commits = get_commits_since_tag(self.project_dir, tag)
        self.commits = commits

        current_ver = parse_current_version(self.project_dir)
        # fallback to tag if file version not found
        if not current_ver and tag:
            current_ver = tag.lstrip("v")

        display_ver = current_ver or "0.0.0"

        status_text = f"Latest Tag: {tag or 'None'} | Commits since tag: {len(commits)} | Current Version: {display_ver}"
        self.query_one("#release-status-lbl", Label).update(status_text)

        # Suggest next version
        next_ver = determine_next_version(display_ver, commits)
        self.query_one("#release-version-input", Input).value = next_ver

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-release-gen":
            self.generate_preview()
        elif event.button.id == "btn-release-exec":
            await self.execute_release()

    def generate_preview(self) -> None:
        new_version = self.query_one("#release-version-input", Input).value
        if not new_version:
            self.notify("Version required.", severity="error")
            return

        self.changelog = generate_changelog(self.commits, new_version)
        editor = self.query_one("#release-changelog-editor", TextArea)
        editor.text = self.changelog

        self.query_one("#btn-release-exec").disabled = False
        self.notify("Changelog generated.")

    async def execute_release(self) -> None:
        new_version = self.query_one("#release-version-input", Input).value
        changelog = self.query_one("#release-changelog-editor", TextArea).text
        dry_run = self.query_one("#chk-release-dry", Checkbox).value

        if not new_version:
            return

        self.notify("Releasing...")
        lbl = self.query_one("#release-result-lbl", Label)
        lbl.update("Releasing...")

        import asyncio
        try:
            success, msg = await asyncio.to_thread(
                perform_release,
                self.project_dir,
                new_version,
                changelog,
                dry_run=dry_run
            )

            if success:
                lbl.update(f"[green]{msg}[/green]")
                self.notify("Release successful!")
                self.load_status() # Refresh
            else:
                lbl.update(f"[red]{msg}[/red]")
                self.notify("Release failed.", severity="error")

        except Exception as e:
            lbl.update(f"[red]Error: {e}[/red]")
            self.notify(f"Error: {e}", severity="error")


class TestGenTab(Container):
    """Tab for generating unit tests."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.selected_file = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: Source File Tree
            with Vertical(id="testgen-list-container", classes="stat-box"):
                yield Label("[bold]Source Files[/bold]")
                yield DirectoryTree(str(self.project_dir), id="testgen-tree")

            # Right Pane: Configuration & Preview
            with Vertical(id="testgen-details-container"):
                yield Label("[bold]Configuration[/bold]")

                with Horizontal(classes="stat-box"):
                    yield Label("Framework:", classes="label")
                    yield Select.from_values(["pytest", "unittest"], id="testgen-framework", value="pytest")
                    yield Label("Agent:", classes="label")
                    yield Select.from_values(["gemini", "cursor", "local"], id="testgen-agent", value="gemini")

                with Horizontal(classes="stat-box"):
                     yield Button("Generate Tests", id="btn-testgen-generate", variant="primary", disabled=True)
                     yield Button("Save Tests", id="btn-testgen-save", variant="success", disabled=True)

                yield Label("[bold]Preview[/bold]")
                yield TextArea(id="testgen-preview", language="python", read_only=False)

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        path = event.path
        if path.is_file():
            self.selected_file = path
            self.query_one("#btn-testgen-generate").disabled = False
            self.notify(f"Selected {path.name}")
        else:
            self.selected_file = None
            self.query_one("#btn-testgen-generate").disabled = True

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-testgen-generate":
            await self.generate_tests()
        elif event.button.id == "btn-testgen-save":
            await self.save_tests()

    async def generate_tests(self) -> None:
        if not self.selected_file:
            return

        framework = self.query_one("#testgen-framework", Select).value or "pytest"
        agent_type = self.query_one("#testgen-agent", Select).value or "gemini"

        preview = self.query_one("#testgen-preview", TextArea)
        preview.text = f"# Generating {framework} tests for {self.selected_file.name}...\n# Please wait."

        self.notify(f"Generating tests with {agent_type}...", severity="information")

        from shared.test_generator import TestGenerator

        generator = TestGenerator(self.project_dir)

        try:
            success, content = await generator.generate_test_code(
                self.selected_file,
                framework=framework,
                agent_type=agent_type
            )

            if success:
                preview.text = content
                self.query_one("#btn-testgen-save").disabled = False
                self.notify("Tests generated.")
            else:
                preview.text = f"# Error generating tests:\n{content}"
                self.notify("Generation failed.", severity="error")

        except Exception as e:
            preview.text = f"# Critical Error:\n{e}"
            self.notify(f"Error: {e}", severity="error")

    async def save_tests(self) -> None:
        if not self.selected_file:
            return

        preview = self.query_one("#testgen-preview", TextArea)
        content = preview.text

        tests_dir = self.project_dir / "tests"
        tests_dir.mkdir(exist_ok=True)
        test_filename = f"test_{self.selected_file.stem}.py"
        output_path = tests_dir / test_filename

        try:
            output_path.write_text(content, encoding="utf-8")
            self.notify(f"Saved to {output_path.name}")
        except Exception as e:
            self.notify(f"Error saving file: {e}", severity="error")


class HealthTab(Container):
    """Tab for project health scorecard."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Label("[bold]Project Health Scorecard[/bold]", classes="welcome-text")

            # Score Header
            with Container(classes="stat-box", id="health-score-container"):
                yield Label("Grade: [bold]?[/bold]", id="health-grade-lbl")
                yield Label("Score: ? / 100", id="health-score-lbl")

            # Breakdown
            with Container(classes="stat-box"):
                yield Label("[bold]Breakdown[/bold]")
                yield DataTable(id="health-breakdown-table")

            # Issues
            with Container(classes="stat-box"):
                yield Label("[bold]Key Issues[/bold]")
                yield ListView(id="health-issues-list")

            # Recommendations
            with Container(classes="stat-box"):
                yield Label("[bold]Recommendations[/bold]")
                yield RichLog(id="health-recommendations-log", wrap=True, highlight=True, markup=True)

            # Actions
            with Horizontal(classes="stat-box"):
                yield Button("Run Health Check", id="btn-run-health", variant="primary")
                yield Label("", id="health-status-lbl")

    def on_mount(self) -> None:
        table = self.query_one("#health-breakdown-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Category", "Score", "Max")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-run-health":
            await self.run_health_check()

    async def run_health_check(self) -> None:
        self.query_one("#health-status-lbl").update("Running health check... (this may take a while)")
        self.notify("Running health check...")

        # Disable button
        self.query_one("#btn-run-health").disabled = True

        import asyncio
        import contextlib
        import io

        def do_calc():
            # Capture stdout to prevent TUI corruption
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                calc = HealthCalculator(self.project_dir)
                calc.calculate()
            return calc

        try:
            calc = await asyncio.to_thread(do_calc)
            self._update_ui(calc)
            self.query_one("#health-status-lbl").update("Health check complete.")
            self.notify("Health check complete.")
        except Exception as e:
            self.query_one("#health-status-lbl").update(f"Error: {e}")
            self.notify(f"Health check failed: {e}", severity="error")
        finally:
            self.query_one("#btn-run-health").disabled = False

    def _update_ui(self, calc: HealthCalculator) -> None:
        # Grade
        grade_color = "red"
        if calc.grade == "A": grade_color = "green"
        elif calc.grade == "B": grade_color = "cyan"
        elif calc.grade == "C": grade_color = "yellow"
        elif calc.grade == "D": grade_color = "orange"

        self.query_one("#health-grade-lbl").update(f"Grade: [bold {grade_color}]{calc.grade}[/]")
        self.query_one("#health-score-lbl").update(f"Score: {calc.score:.0f} / 100")

        # Breakdown
        table = self.query_one("#health-breakdown-table", DataTable)
        table.clear()
        table.add_row("Tests", str(calc.metrics['test_score']), "30")
        table.add_row("Linting", str(calc.metrics['lint_score']), "20")
        table.add_row("Complexity", str(calc.metrics['complexity_score']), "20")
        table.add_row("Security", str(calc.metrics['security_score']), "20")
        table.add_row("Dependencies", str(calc.metrics['dependency_score']), "10")

        # Issues
        issues_list = self.query_one("#health-issues-list", ListView)
        issues_list.clear()
        if calc.issues:
            for issue in calc.issues:
                issues_list.append(ListItem(Label(f"⚠️ {issue}")))
        else:
            issues_list.append(ListItem(Label("[green]No significant issues found.[/green]")))

        # Recommendations
        rec_log = self.query_one("#health-recommendations-log", RichLog)
        rec_log.clear()

        if calc.metrics['test_score'] < 30:
            rec_log.write("- Fix failing tests or add more test coverage.")
        if calc.metrics['lint_score'] < 20:
            rec_log.write("- Run 'verify --fix' to resolve linting issues.")
        if calc.metrics['complexity_score'] < 20:
            rec_log.write("- Refactor complex functions (use 'polish' command).")
        if calc.metrics['security_score'] < 20:
            rec_log.write("- Address security vulnerabilities (use 'security' command).")
        if calc.metrics['dependency_score'] < 10:
            rec_log.write("- Update dependencies (use 'deps --update').")

        if calc.score == 100:
            rec_log.write("[bold green]Great job! Keep it up.[/bold green]")


class TroubleshootTab(Container):
    """Tab for interactive troubleshooting."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = TroubleshootManager(project_dir)
        self.issues = {}

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Troubleshooting Assistant[/bold]", classes="welcome-text")

            # Controls
            with Horizontal(classes="stat-box"):
                yield Button("Analyze Project", id="btn-analyze", variant="primary")
                yield Select.from_values(["gemini", "cursor", "local"], id="troubleshoot-agent", value="gemini")
                yield Label("User Report (Optional):")
                yield Input(placeholder="Describe the issue...", id="troubleshoot-issue")

            # Results
            with Vertical(id="troubleshoot-results-container", classes="stat-box"):
                yield Label("[bold]Detected Issues[/bold]")
                yield DataTable(id="troubleshoot-table")

            # Diagnosis & Plan
            with VerticalScroll(id="troubleshoot-diagnosis-container"):
                yield Label("[bold]AI Diagnosis & Plan[/bold]")
                yield Markdown("Run analysis and diagnosis to see AI plan.", id="troubleshoot-markdown")

            # Actions
            with Horizontal(classes="stat-box"):
                yield Button("Diagnose with AI", id="btn-diagnose", variant="warning", disabled=True)
                yield Button("Apply Fix", id="btn-fix", variant="success", disabled=True)
                yield Button("Verify", id="btn-verify", variant="default", disabled=True)
                yield Button("Learn", id="btn-learn", variant="primary", disabled=True)

    def on_mount(self) -> None:
        table = self.query_one("#troubleshoot-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Check", "Status", "Details")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-analyze":
            await self.run_analysis()
        elif event.button.id == "btn-diagnose":
            await self.run_diagnosis()
        elif event.button.id == "btn-fix":
            await self.run_fix()
        elif event.button.id == "btn-verify":
            await self.run_verify()
        elif event.button.id == "btn-learn":
            await self.learn_solution()

    async def run_analysis(self) -> None:
        table = self.query_one("#troubleshoot-table", DataTable)
        table.clear()
        self.notify("Running analysis... (this may take a while)")

        import asyncio

        # Run detection in thread
        self.issues = await asyncio.to_thread(self.manager.detect_issues)

        if not self.issues:
            self.notify("No automated issues found.")
            table.add_row("All Checks", "[green]PASSED[/green]", "No issues detected.")
        else:
            self.notify(f"Found {len(self.issues)} issues.")
            for check, res in self.issues.items():
                status = "[red]FAILED[/red]"
                details = res.get("stderr", "") or res.get("stdout", "")
                # Truncate details
                if len(details) > 100:
                    details = details[:97] + "..."
                table.add_row(check.upper(), status, details)

        # Enable diagnosis regardless of issues (user might have manual report)
        self.query_one("#btn-diagnose").disabled = False

    async def run_diagnosis(self) -> None:
        user_issue = self.query_one("#troubleshoot-issue", Input).value
        if not self.issues and not user_issue:
            self.notify("No issues to diagnose.", severity="warning")
            return

        agent_type = self.query_one("#troubleshoot-agent", Select).value or "gemini"

        # Re-init manager with selected agent
        self.manager = TroubleshootManager(self.project_dir, agent_type=agent_type)

        self.notify(f"Diagnosing with {agent_type}...", severity="information")
        md_view = self.query_one("#troubleshoot-markdown", Markdown)
        md_view.update("Thinking... please wait.")

        try:
            response = await self.manager.diagnose(self.issues, user_query=user_issue)
            md_view.update(response)
            self.notify("Diagnosis complete.")

            self.query_one("#btn-fix").disabled = False
            self.query_one("#btn-verify").disabled = False
            self.query_one("#btn-learn").disabled = False

        except Exception as e:
            md_view.update(f"Error: {e}")
            self.notify(f"Diagnosis failed: {e}", severity="error")

    async def run_fix(self) -> None:
        self.notify("Applying fix...", severity="information")
        try:
            result = await self.manager.apply_fix()
            self.query_one("#troubleshoot-markdown", Markdown).update(result + "\\n\\nFix Applied.")
            self.notify("Fix applied.")
        except Exception as e:
            self.notify(f"Fix failed: {e}", severity="error")

    async def run_verify(self) -> None:
        # Re-run analysis
        await self.run_analysis()
        if not self.issues:
            self.notify("Verification passed! Issues resolved.")
        else:
            self.notify("Issues still persist.", severity="warning")

    async def learn_solution(self) -> None:
        user_issue = self.query_one("#troubleshoot-issue", Input).value
        summary = user_issue or "Automated Issues"
        try:
            self.manager.learn(summary, "Fixed via TUI")
            self.notify("Solution saved to Knowledge Base.")
        except Exception as e:
            self.notify(f"Learn failed: {e}", severity="error")


class DocumentationTab(Container):
    """Tab for managing project documentation."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.docstring_mgr = DocstringManager(project_dir)
        self.link_checker = LinkChecker()
        self.openapi_gen = OpenAPIGenerator(project_dir)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Documentation Hub[/bold]", classes="welcome-text")

            with TabbedContent():
                with TabPane("Overview"):
                    with Vertical():
                        with Horizontal(classes="stat-box"):
                            yield Button("Save README", id="btn-docs-save-readme", variant="success")
                            yield Button("Preview", id="btn-docs-preview-readme", variant="default")
                        yield TextArea(id="readme-editor", language="markdown")
                        yield Markdown(id="readme-preview", classes="hidden")

                with TabPane("Docstrings"):
                    with Vertical():
                        with Horizontal(classes="stat-box"):
                            yield Button("Scan Missing", id="btn-docs-scan-docstrings", variant="primary")
                            yield Button("Generate All", id="btn-docs-gen-docstrings", variant="warning")
                            yield Select.from_values(["gemini", "cursor", "local"], id="docs-agent-select", value="gemini")
                        yield DataTable(id="docstring-table")
                        yield RichLog(id="docstring-log", wrap=True, highlight=True, markup=True)

                with TabPane("Links"):
                    with Vertical():
                        with Horizontal(classes="stat-box"):
                            yield Button("Check Links", id="btn-docs-check-links", variant="primary")
                        yield DataTable(id="links-table")

                with TabPane("OpenAPI"):
                    with Vertical():
                        with Horizontal(classes="stat-box"):
                            yield Button("Generate Spec", id="btn-docs-gen-openapi", variant="warning")
                            yield Button("Save Spec", id="btn-docs-save-openapi", variant="success")
                        yield TextArea(id="openapi-editor", language="yaml")

    def on_mount(self) -> None:
        # Load README
        self.load_readme()

        # Init Tables
        ds_table = self.query_one("#docstring-table", DataTable)
        ds_table.cursor_type = "row"
        ds_table.add_columns("File", "Name", "Type", "Line")

        links_table = self.query_one("#links-table", DataTable)
        links_table.cursor_type = "row"
        links_table.add_columns("File", "Line", "URL", "Status/Error")

    def load_readme(self) -> None:
        readme_path = self.project_dir / "README.md"
        editor = self.query_one("#readme-editor", TextArea)
        if readme_path.exists():
            editor.text = readme_path.read_text(encoding="utf-8", errors="replace")
        else:
            editor.text = "# New Project"

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-docs-save-readme":
            self.save_readme()
        elif event.button.id == "btn-docs-preview-readme":
            self.toggle_readme_preview()
        elif event.button.id == "btn-docs-scan-docstrings":
            self.scan_docstrings()
        elif event.button.id == "btn-docs-gen-docstrings":
            await self.generate_docstrings()
        elif event.button.id == "btn-docs-check-links":
            await self.check_links()
        elif event.button.id == "btn-docs-gen-openapi":
            await self.generate_openapi()
        elif event.button.id == "btn-docs-save-openapi":
            self.save_openapi()

    def save_readme(self) -> None:
        content = self.query_one("#readme-editor", TextArea).text
        path = self.project_dir / "README.md"
        try:
            path.write_text(content, encoding="utf-8")
            self.notify("README.md saved.")
        except Exception as e:
            self.notify(f"Error saving README: {e}", severity="error")

    def toggle_readme_preview(self) -> None:
        editor = self.query_one("#readme-editor", TextArea)
        preview = self.query_one("#readme-preview", Markdown)

        if editor.has_class("hidden"):
            editor.remove_class("hidden")
            preview.add_class("hidden")
        else:
            preview.update(editor.text)
            editor.add_class("hidden")
            preview.remove_class("hidden")

    def scan_docstrings(self) -> None:
        table = self.query_one("#docstring-table", DataTable)
        table.clear()

        items = self.docstring_mgr.scan()
        self.notify(f"Found {len(items)} missing docstrings.")

        for item in items:
            rel_path = item["file"].relative_to(self.project_dir)
            table.add_row(str(rel_path), item["name"], item["type"], str(item["lineno"]))

    async def generate_docstrings(self) -> None:
        agent_type = self.query_one("#docs-agent-select", Select).value or "gemini"

        # Re-scan to be safe
        items = self.docstring_mgr.scan()
        if not items:
            self.notify("No missing docstrings found.")
            return

        log = self.query_one("#docstring-log", RichLog)
        log.write(f"Generating docstrings for {len(items)} items with {agent_type}...")

        import contextlib

        # Capture stdout from manager
        output_capture = io.StringIO()
        count = 0

        try:
            with contextlib.redirect_stdout(output_capture):
                count = await self.docstring_mgr.generate_and_apply(items, agent_type=agent_type)
        except Exception as e:
            output_capture.write(f"Error: {e}")

        log.write(output_capture.getvalue())
        log.write(f"Applied {count} docstrings.")
        self.notify(f"Generated {count} docstrings.")
        self.scan_docstrings() # Refresh table

    async def check_links(self) -> None:
        table = self.query_one("#links-table", DataTable)
        table.clear()
        self.notify("Checking links... (this may take a while)")

        import asyncio

        # Resolve files (all .md files)
        files = list(self.project_dir.rglob("*.md"))

        if not files:
            self.notify("No markdown files found.")
            return

        try:
            # Run in thread
            # check_files returns a dict report
            result = await asyncio.to_thread(self.link_checker.check_files, files)

            if result["broken_links_count"] == 0:
                self.notify("All links are valid!")
            else:
                self.notify(f"Found {result['broken_links_count']} broken links.", severity="warning")

                for p, issues in result["details"].items():
                    rel_path = p.relative_to(self.project_dir)
                    for issue in issues:
                        status = f"Status: {issue['status']}" if issue['status'] > 0 else f"Error: {issue['error']}"
                        table.add_row(str(rel_path), str(issue['line']), issue['url'], status)

        except Exception as e:
            self.notify(f"Link check error: {e}", severity="error")

    async def generate_openapi(self) -> None:
        self.notify("Generating OpenAPI spec...")
        output_path = self.project_dir / "openapi.yaml"

        success = await self.openapi_gen.generate(output_path)

        if success:
            self.notify("Spec generated.")
            if output_path.exists():
                self.query_one("#openapi-editor", TextArea).text = output_path.read_text(encoding="utf-8")
        else:
            self.notify("Failed to generate spec.", severity="error")

    def save_openapi(self) -> None:
        content = self.query_one("#openapi-editor", TextArea).text
        path = self.project_dir / "openapi.yaml"
        try:
            path.write_text(content, encoding="utf-8")
            self.notify("openapi.yaml saved.")
        except Exception as e:
            self.notify(f"Error saving spec: {e}", severity="error")


class ConfigTab(Container):
    """Tab for managing agent configuration."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.config_path = self.project_dir / "agent_config.yaml"

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Label("[bold]Agent Configuration[/bold]", classes="welcome-text")

            # General Settings
            with Container(classes="stat-box"):
                yield Label("[bold]General Settings[/bold]")
                yield Label("Agent Type:")
                yield Select.from_values(["gemini", "cursor", "local", "openrouter"], id="cfg-agent-type", value="gemini")
                yield Label("Model:")
                yield Input(placeholder="e.g. gemini-1.5-pro", id="cfg-model")
                yield Label("Max Iterations (optional):")
                yield Input(placeholder="e.g. 50", id="cfg-max-iterations", type="integer")
                yield Label("Manager Frequency (iterations):")
                yield Input(placeholder="e.g. 10", id="cfg-manager-freq", type="integer")

            # Notifications
            with Container(classes="stat-box"):
                yield Label("[bold]Notifications[/bold]")
                yield Label("Slack Webhook URL:")
                yield Input(placeholder="https://hooks.slack.com/...", id="cfg-slack")
                yield Label("Discord Webhook URL:")
                yield Input(placeholder="https://discord.com/api/...", id="cfg-discord")

                yield Label("Events:")
                with Vertical():
                    yield Checkbox("Iteration Summary", id="cfg-notify-iteration")
                    yield Checkbox("Manager Updates", id="cfg-notify-manager")
                    yield Checkbox("Human in Loop", id="cfg-notify-human")
                    yield Checkbox("Project Completion", id="cfg-notify-completion")
                    yield Checkbox("Errors", id="cfg-notify-error")

            # Jira Integration
            with Container(classes="stat-box"):
                yield Label("[bold]Jira Integration[/bold]")
                yield Label("Jira URL:")
                yield Input(placeholder="https://your-domain.atlassian.net", id="cfg-jira-url")
                yield Label("Email:")
                yield Input(placeholder="user@example.com", id="cfg-jira-email")
                yield Label("API Token:")
                yield Input(placeholder="Token...", id="cfg-jira-token", password=True)

            # Actions
            with Horizontal(classes="stat-box"):
                yield Button("Save Configuration", id="btn-cfg-save", variant="primary")
                yield Button("Reload", id="btn-cfg-reload", variant="default")

    def on_mount(self) -> None:
        self.load_config()

    def load_config(self) -> None:
        # We can use load_config_from_file without arguments to search
        # It will resolve project dir if we run from it, or XDG
        # But we want to prioritize what's actually being used.
        # Ideally we load from self.config_path if exists, else fallback.

        config = {}
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    config = yaml.safe_load(f) or {}
            except Exception:
                pass

        if not config:
             config = load_config_from_file()

        # Populate fields
        self.query_one("#cfg-agent-type", Select).value = config.get("agent_type", "gemini")
        self.query_one("#cfg-model", Input).value = config.get("model") or ""
        self.query_one("#cfg-max-iterations", Input).value = str(config.get("max_iterations") or "")
        self.query_one("#cfg-manager-freq", Input).value = str(config.get("manager_frequency") or 10)

        self.query_one("#cfg-slack", Input).value = config.get("slack_webhook_url") or ""
        self.query_one("#cfg-discord", Input).value = config.get("discord_webhook_url") or ""

        notif = config.get("notification_settings", {}) or {}
        self.query_one("#cfg-notify-iteration", Checkbox).value = notif.get("iteration", False)
        self.query_one("#cfg-notify-manager", Checkbox).value = notif.get("manager", True)
        self.query_one("#cfg-notify-human", Checkbox).value = notif.get("human_in_loop", True)
        self.query_one("#cfg-notify-completion", Checkbox).value = notif.get("project_completion", True)
        self.query_one("#cfg-notify-error", Checkbox).value = notif.get("error", True)

        jira = config.get("jira", {}) or {}
        self.query_one("#cfg-jira-url", Input).value = jira.get("url") or ""
        self.query_one("#cfg-jira-email", Input).value = jira.get("email") or ""
        self.query_one("#cfg-jira-token", Input).value = jira.get("token") or ""

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cfg-save":
            self.save_config()
        elif event.button.id == "btn-cfg-reload":
            self.load_config()
            self.notify("Configuration reloaded.")

    def save_config(self) -> None:
        # Load existing config to preserve other keys
        config = {}
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    config = yaml.safe_load(f) or {}
            except Exception:
                pass

        # Update with widget values
        config["agent_type"] = self.query_one("#cfg-agent-type", Select).value

        model = self.query_one("#cfg-model", Input).value
        if model: config["model"] = model

        max_iter = self.query_one("#cfg-max-iterations", Input).value
        if max_iter and max_iter.isdigit(): config["max_iterations"] = int(max_iter)

        mgr_freq = self.query_one("#cfg-manager-freq", Input).value
        if mgr_freq and mgr_freq.isdigit(): config["manager_frequency"] = int(mgr_freq)

        slack = self.query_one("#cfg-slack", Input).value
        if slack: config["slack_webhook_url"] = slack

        discord = self.query_one("#cfg-discord", Input).value
        if discord: config["discord_webhook_url"] = discord

        notif = {
            "iteration": self.query_one("#cfg-notify-iteration", Checkbox).value,
            "manager": self.query_one("#cfg-notify-manager", Checkbox).value,
            "human_in_loop": self.query_one("#cfg-notify-human", Checkbox).value,
            "project_completion": self.query_one("#cfg-notify-completion", Checkbox).value,
            "error": self.query_one("#cfg-notify-error", Checkbox).value,
        }
        config["notification_settings"] = notif

        jira_url = self.query_one("#cfg-jira-url", Input).value
        jira_email = self.query_one("#cfg-jira-email", Input).value
        jira_token = self.query_one("#cfg-jira-token", Input).value

        if jira_url:
            config["jira"] = {
                "url": jira_url,
                "email": jira_email,
                "token": jira_token
            }

        try:
            with open(self.config_path, "w") as f:
                yaml.dump(config, f, sort_keys=False, indent=2)
            # Set permissions
            os.chmod(self.config_path, 0o600)
            self.notify(f"Configuration saved to {self.config_path}")
        except Exception as e:
            self.notify(f"Error saving configuration: {e}", severity="error")


class CostTab(Container):
    """Tab for monitoring costs."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.calculator = CostCalculator(project_dir)

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Label("[bold]Cost Management[/bold]", classes="welcome-text")

            # Budget Status
            with Container(classes="stat-box"):
                yield Label("[bold]Budget Status[/bold]")
                yield Label("Loading...", id="cost-budget-lbl")
                yield Label("Remaining: ", id="cost-remaining-lbl")

            # Chart
            with Container(classes="stat-box"):
                yield Label("[bold]Cost History[/bold]")
                yield RichLog(id="cost-chart-log", wrap=False, highlight=False)

            # Details
            with Container(classes="stat-box"):
                yield Label("[bold]Run Details[/bold]")
                yield DataTable(id="cost-table")

            # Actions
            with Horizontal(classes="stat-box"):
                yield Button("Refresh", id="btn-cost-refresh", variant="primary")

    def on_mount(self) -> None:
        table = self.query_one("#cost-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Run ID", "Model", "Total Tokens", "Cost ($)")
        self.refresh_data()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cost-refresh":
            self.refresh_data()
            self.notify("Cost data refreshed.")

    def refresh_data(self) -> None:
        import asyncio
        asyncio.create_task(self._load_data())

    async def _load_data(self) -> None:
        import asyncio
        data = await asyncio.to_thread(self.calculator.calculate_total_cost)
        budget = await asyncio.to_thread(self.calculator.check_budget)

        self._update_ui(data, budget)

    def _update_ui(self, data: dict, budget: dict) -> None:
        # Update Budget
        status = budget["status"]
        status_color = "green"
        if status == "WARNING": status_color = "yellow"
        elif status == "EXCEEDED": status_color = "red"
        elif status == "No Limit": status_color = "blue"

        if status == "No Limit":
             self.query_one("#cost-budget-lbl").update(f"Status: [bold {status_color}]{status}[/]")
             self.query_one("#cost-remaining-lbl").update(f"Total Spent: ${budget.get('current', 0.0):.4f}")
        else:
             self.query_one("#cost-budget-lbl").update(f"Status: [bold {status_color}]{status}[/] ({budget['percent']:.1f}%)")
             self.query_one("#cost-remaining-lbl").update(f"Remaining: ${budget['remaining']:.4f} / ${budget['limit']:.2f}")

        # Update Table
        table = self.query_one("#cost-table", DataTable)
        table.clear()

        # Details are in data['details'] list of dicts
        details = data.get("details", [])
        # Show latest first
        for run in reversed(details):
            if "error" in run:
                continue

            total_tokens = run["input_tokens"] + run["output_tokens"]
            table.add_row(
                run["run_id"],
                run["model"],
                f"{int(total_tokens):,}",
                f"${run['total_cost']:.4f}"
            )

        # Update Chart
        chart_log = self.query_one("#cost-chart-log", RichLog)
        chart_log.clear()

        # Prepare data for chart (last 10 runs)
        chart_data = {}
        for run in details[-10:]:
             if "error" in run: continue
             # Use short ID
             label = run["run_id"][-6:] if len(run["run_id"]) > 6 else run["run_id"]
             chart_data[label] = run["total_cost"]

        if chart_data:
            chart = draw_ascii_bar_chart(chart_data, "Recent Run Costs ($)")
            chart_log.write(chart)
        else:
            chart_log.write("No data for chart.")


class PromptLabTab(Container):
    """Tab for prompt engineering experiments."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = PromptLabManager(project_dir)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Prompt Lab[/bold]", classes="welcome-text")

            # Configuration
            with Horizontal(classes="stat-box"):
                with Vertical(id="pl-config-pane"):
                    yield Label("Agents:")
                    yield Checkbox("Gemini", id="pl-chk-gemini", value=True)
                    yield Checkbox("Cursor", id="pl-chk-cursor", value=False)
                    yield Checkbox("Local", id="pl-chk-local", value=False)
                    yield Button("Run Experiment", id="btn-pl-run", variant="primary")

                with Vertical(id="pl-save-pane"):
                    yield Input(placeholder="Experiment Name...", id="pl-exp-name")
                    with Horizontal():
                        yield Button("Save", id="btn-pl-save", variant="success")
                        yield Button("Load", id="btn-pl-load", variant="warning")
                    yield Select([], id="pl-exp-select", prompt="Select Experiment")

            # Prompts
            with Horizontal():
                with Vertical(classes="stat-box"):
                    yield Label("System Prompt (Context)")
                    yield TextArea(id="pl-system-prompt")
                with Vertical(classes="stat-box"):
                    yield Label("User Prompt (Instruction)")
                    yield TextArea(id="pl-user-prompt")

            # Results
            yield Label("[bold]Results[/bold]")
            with TabbedContent(id="pl-results-tabs"):
                with TabPane("Gemini", id="pl-tab-gemini"):
                    yield RichLog(id="pl-res-gemini", wrap=True, markup=True)
                with TabPane("Cursor", id="pl-tab-cursor"):
                    yield RichLog(id="pl-res-cursor", wrap=True, markup=True)
                with TabPane("Local", id="pl-tab-local"):
                    yield RichLog(id="pl-res-local", wrap=True, markup=True)

    def on_mount(self) -> None:
        self.refresh_experiments()

    def refresh_experiments(self) -> None:
        exps = self.manager.list_experiments()
        select = self.query_one("#pl-exp-select", Select)
        select.set_options([(e, e) for e in exps])

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-pl-run":
            await self.run_experiment()
        elif event.button.id == "btn-pl-save":
            self.save_experiment()
        elif event.button.id == "btn-pl-load":
            self.load_experiment()

    async def run_experiment(self) -> None:
        sys_prompt = self.query_one("#pl-system-prompt", TextArea).text
        user_prompt = self.query_one("#pl-user-prompt", TextArea).text

        agents = []
        if self.query_one("#pl-chk-gemini", Checkbox).value:
            agents.append("gemini")
        if self.query_one("#pl-chk-cursor", Checkbox).value:
            agents.append("cursor")
        if self.query_one("#pl-chk-local", Checkbox).value:
            agents.append("local")

        if not agents:
            self.notify("Select at least one agent.", severity="error")
            return

        self.notify(f"Running experiment on {', '.join(agents)}...", severity="information")

        # Clear logs
        for agent in ["gemini", "cursor", "local"]:
            try:
                self.query_one(f"#pl-res-{agent}", RichLog).clear()
            except Exception:
                pass

        results = await self.manager.run_experiment(sys_prompt, user_prompt, agents)

        for agent, response in results.items():
            try:
                log = self.query_one(f"#pl-res-{agent}", RichLog)
                log.write(response)
            except Exception:
                pass

        self.notify("Experiment complete.")

    def save_experiment(self) -> None:
        name = self.query_one("#pl-exp-name", Input).value
        if not name:
            self.notify("Name required.", severity="error")
            return

        data = {
            "system_prompt": self.query_one("#pl-system-prompt", TextArea).text,
            "user_prompt": self.query_one("#pl-user-prompt", TextArea).text,
            "agents": {
                "gemini": self.query_one("#pl-chk-gemini", Checkbox).value,
                "cursor": self.query_one("#pl-chk-cursor", Checkbox).value,
                "local": self.query_one("#pl-chk-local", Checkbox).value,
            }
        }
        self.manager.save_experiment(name, data)
        self.notify(f"Saved '{name}'.")
        self.refresh_experiments()

    def load_experiment(self) -> None:
        select = self.query_one("#pl-exp-select", Select)
        name = select.value
        if not name:
            self.notify("Select an experiment to load.", severity="warning")
            return

        data = self.manager.load_experiment(name)
        if not data:
            self.notify("Experiment not found.", severity="error")
            return

        self.query_one("#pl-system-prompt", TextArea).text = data.get("system_prompt", "")
        self.query_one("#pl-user-prompt", TextArea).text = data.get("user_prompt", "")

        agents = data.get("agents", {})
        self.query_one("#pl-chk-gemini", Checkbox).value = agents.get("gemini", False)
        self.query_one("#pl-chk-cursor", Checkbox).value = agents.get("cursor", False)
        self.query_one("#pl-chk-local", Checkbox).value = agents.get("local", False)

        self.query_one("#pl-exp-name", Input).value = name
        self.notify(f"Loaded '{name}'.")


class RefactorTab(Container):
    """Tab for interactive AI refactoring."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = RefactorManager(project_dir)
        self.selected_file = None
        self.preview_data = {}  # Store result from refactor_file

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: File Tree
            with Vertical(id="refactor-tree-container", classes="stat-box"):
                yield Label("[bold]Select File[/bold]")
                yield DirectoryTree(str(self.project_dir), id="refactor-file-tree")

            # Right Pane: Controls & Preview
            with Vertical(id="refactor-main-container"):
                yield Label("[bold]Refactoring Controls[/bold]")

                with Vertical(classes="stat-box"):
                    yield Label("Instruction:")
                    yield Input(placeholder="e.g. Extract class, Rename variable...", id="refactor-instruction")

                    with Horizontal():
                        yield Select.from_values(["gemini", "cursor", "local"], id="refactor-agent-select", value="gemini")
                        yield Button("Preview Refactor", id="btn-refactor-preview", variant="primary", disabled=True)
                        yield Button("Apply Changes", id="btn-refactor-apply", variant="success", disabled=True)

                yield Label("[bold]Diff Preview[/bold]")
                yield RichLog(id="refactor-diff-log", wrap=True, highlight=True, markup=True)

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        if event.path.is_file():
            self.selected_file = event.path
            self.query_one("#btn-refactor-preview").disabled = False
            self.notify(f"Selected {event.path.name}")
        else:
            self.selected_file = None
            self.query_one("#btn-refactor-preview").disabled = True

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-refactor-preview":
            await self.preview_refactor()
        elif event.button.id == "btn-refactor-apply":
            self.apply_changes()

    async def preview_refactor(self) -> None:
        if not self.selected_file:
            return

        instruction = self.query_one("#refactor-instruction", Input).value
        if not instruction:
            self.notify("Instruction required.", severity="error")
            return

        agent_type = self.query_one("#refactor-agent-select", Select).value or "gemini"
        log = self.query_one("#refactor-diff-log", RichLog)

        log.clear()
        log.write(f"Refactoring {self.selected_file.name} with {agent_type}...")
        self.notify("Generating preview...", severity="information")

        try:
            # refactor_file returns dict with keys: original_content, new_content, diff, changed
            self.preview_data = await self.manager.refactor_file(
                self.selected_file,
                instruction,
                agent_type=agent_type
            )

            log.clear()
            if self.preview_data["changed"]:
                log.write(Syntax(self.preview_data["diff"], "diff", theme="monokai"))
                self.query_one("#btn-refactor-apply").disabled = False
                self.notify("Preview generated.")
            else:
                log.write("No changes suggested by AI.")
                self.query_one("#btn-refactor-apply").disabled = True

        except Exception as e:
            log.write(f"[bold red]Error:[/bold red] {e}")
            self.notify(f"Refactor failed: {e}", severity="error")

    def apply_changes(self) -> None:
        if not self.preview_data or not self.selected_file:
            return

        try:
            self.manager.apply_changes(self.selected_file, self.preview_data["new_content"])
            self.notify(f"Changes applied to {self.selected_file.name}")
            self.query_one("#refactor-diff-log", RichLog).write("\n[bold green]Changes Applied![/bold green]")
            self.query_one("#btn-refactor-apply").disabled = True
            self.preview_data = {} # Reset
        except Exception as e:
            self.notify(f"Error applying changes: {e}", severity="error")


class AgentTUI(App):
    """Mission Control TUI."""

    CSS_PATH = "tui.css"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "toggle_dark", "Toggle Dark Mode"),
        ("f1", "toggle_command_palette", "Command Palette"),
    ]

    PALETTE_COMMANDS = [
        PaletteCommand("Go to Dashboard", "switch_tab_dashboard"),
        PaletteCommand("Go to Monitor", "switch_tab_monitor"),
        PaletteCommand("Go to Terminal", "switch_tab_terminal"),
        PaletteCommand("Go to K8s", "switch_tab_k8s"),
        PaletteCommand("Go to Explorer", "switch_tab_explorer"),
        PaletteCommand("Go to Disk Usage", "switch_tab_disk_usage"),
        PaletteCommand("Go to Logs", "switch_tab_logs"),
        PaletteCommand("Go to Chat", "switch_tab_interact"),
        PaletteCommand("Go to Tasks", "switch_tab_tasks"),
        PaletteCommand("Go to Git", "switch_tab_git"),
        PaletteCommand("Go to Config", "switch_tab_config"),
        PaletteCommand("Go to IDE Config", "switch_tab_ide_config"),
        PaletteCommand("Go to DevTools", "switch_tab_devtools"),
        PaletteCommand("Refresh Dashboard", "refresh_dashboard"),
        PaletteCommand("Run Tests", "run_tests"),
        PaletteCommand("Run Lint", "run_lint"),
        PaletteCommand("Toggle Dark Mode", "toggle_dark"),
        PaletteCommand("Quit", "quit"),
    ]

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.plugin_manager = PluginManager(project_dir)
        self.plugin_manager.load_plugins()

    def action_toggle_command_palette(self) -> None:
        self.push_screen(AgentCommandPalette(self.PALETTE_COMMANDS), self.on_command_palette_selected)

    def on_command_palette_selected(self, command: PaletteCommand | None) -> None:
        if not command:
            return

        action = command.action
        if callable(action):
            action()
        elif isinstance(action, str):
            if action.startswith("switch_tab_"):
                tab_id = action.replace("switch_tab_", "tab-")
                self.query_one("#main-tabs", TabbedContent).active = tab_id
            elif action == "refresh_dashboard":
                self.action_refresh_dashboard()
            elif action == "run_tests":
                self.action_run_tests()
            elif action == "run_lint":
                self.action_run_lint()
            elif action == "toggle_dark":
                self.action_toggle_dark()
            elif action == "quit":
                self.run_worker(self.action_quit())
            else:
                self.notify(f"Unknown action: {action}", severity="warning")

    def action_refresh_dashboard(self) -> None:
        self.query_one(DashboardTab).update_history()
        self.notify("Dashboard refreshed.")

    def action_run_tests(self) -> None:
        import subprocess
        self.notify("Running tests...")
        try:
            subprocess.Popen([sys.executable, "main.py", "test", "-p", str(self.project_dir)])
            self.notify("Tests started in background.")
        except Exception as e:
            self.notify(f"Failed to start tests: {e}", severity="error")

    def action_run_lint(self) -> None:
        import subprocess
        self.notify("Running lint...")
        try:
            subprocess.Popen([sys.executable, "main.py", "lint", "-p", str(self.project_dir)])
            self.notify("Lint started in background.")
        except Exception as e:
            self.notify(f"Failed to start lint: {e}", severity="error")

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(id="main-tabs"):
            with TabPane("Dashboard", id="tab-dashboard"):
                yield DashboardTab(self.project_dir)
            with TabPane("Monitor", id="tab-monitor"):
                yield SystemMonitorTab(self.project_dir)
            with TabPane("Terminal", id="tab-terminal"):
                yield TerminalTab(self.project_dir)
            with TabPane("Services", id="tab-services"):
                yield ServicesTab(self.project_dir)
            with TabPane("Processes", id="tab-proc"):
                yield ProcLabTab(self.project_dir)
            with TabPane("Docker", id="tab-docker"):
                yield DockerTab(self.project_dir)
            with TabPane("K8s", id="tab-k8s"):
                yield K8sTab(self.project_dir)
            with TabPane("Terraform", id="tab-terraform"):
                yield TerraformTab(self.project_dir)
            with TabPane("Chaos", id="tab-chaos"):
                yield ChaosTab(self.project_dir)
            with TabPane("Scheduler", id="tab-scheduler"):
                yield SchedulerTab(self.project_dir)
            with TabPane("Config", id="tab-config"):
                yield ConfigTab(self.project_dir)
            with TabPane("IDE Config", id="tab-ide-config"):
                yield IdeConfigTab(self.project_dir)
            with TabPane("Docs", id="tab-docs"):
                yield DocumentationTab(self.project_dir)
            with TabPane("ADRs", id="tab-adr"):
                yield ADRTab(self.project_dir)
            with TabPane("Test Gen", id="tab-test-gen"):
                yield TestGenTab(self.project_dir)
            with TabPane("Scaffold", id="tab-scaffold"):
                yield ScaffoldTab(self.project_dir)
            with TabPane("Refactor", id="tab-refactor"):
                yield RefactorTab(self.project_dir)
            with TabPane("Plan", id="tab-plan"):
                yield PlanTab(self.project_dir)
            with TabPane("Interact", id="tab-interact"):
                yield InteractTab(self.project_dir)
            with TabPane("Research", id="tab-research"):
                yield ResearchTab(self.project_dir)
            with TabPane("Recipes", id="tab-recipes"):
                yield RecipesTab(self.project_dir)
            with TabPane("Code Review", id="tab-code-review"):
                yield CodeReviewTab(self.project_dir)
            with TabPane("Search", id="tab-search"):
                yield SearchTab(self.project_dir)
            with TabPane("Tasks", id="tab-tasks"):
                yield TasksTab(self.project_dir)
            with TabPane("Gantt", id="tab-gantt"):
                yield GanttTab(self.project_dir)
            with TabPane("Standup", id="tab-standup"):
                yield StandupTab(self.project_dir)
            with TabPane("Git", id="tab-git"):
                yield GitTab(self.project_dir)
            with TabPane("Pull Requests", id="tab-pr"):
                yield PullRequestsTab(self.project_dir)
            with TabPane("Conflicts", id="tab-conflicts"):
                yield ConflictTab(self.project_dir)
            with TabPane("Bisect", id="tab-bisect"):
                yield BisectTab(self.project_dir)
            with TabPane("Release", id="tab-release"):
                yield ReleaseTab(self.project_dir)
            with TabPane("Worktrees", id="tab-worktrees"):
                yield WorktreesTab(self.project_dir)
            with TabPane("Dependencies", id="tab-deps"):
                yield DependenciesTab(self.project_dir)
            with TabPane("Analytics", id="tab-analytics"):
                yield AnalyticsTab(self.project_dir)
            with TabPane("Security", id="tab-security"):
                yield SecurityTab(self.project_dir)
            with TabPane("Guardrails", id="tab-guardrails"):
                yield GuardrailsTab(self.project_dir)
            with TabPane("Health", id="tab-health"):
                yield HealthTab(self.project_dir)
            with TabPane("Impact", id="tab-impact"):
                yield ImpactTab(self.project_dir)
            with TabPane("Troubleshoot", id="tab-troubleshoot"):
                yield TroubleshootTab(self.project_dir)
            with TabPane("Sentinel", id="tab-sentinel"):
                yield SentinelTab(self.project_dir)
            with TabPane("Knowledge", id="tab-knowledge"):
                yield KnowledgeTab(self.project_dir)
            with TabPane("Explorer", id="tab-explorer"):
                yield FileExplorerTab(self.project_dir)
            with TabPane("Disk Usage", id="tab-disk-usage"):
                yield DiskUsageTab(self.project_dir)
            with TabPane("Code Map", id="tab-codemap"):
                yield CodeMapTab(self.project_dir)
            with TabPane("Network", id="tab-network"):
                yield NetworkTab(self.project_dir)
            with TabPane("Net Diag", id="tab-net-diag"):
                yield NetDiagTab(self.project_dir)
            with TabPane("Snippets", id="tab-snippets"):
                yield SnippetsTab(self.project_dir)
            with TabPane("Profiler", id="tab-profile"):
                yield ProfileTab(self.project_dir)
            with TabPane("Sessions", id="tab-sessions"):
                yield SessionTab(self.project_dir)
            with TabPane("Timeline", id="tab-timeline"):
                yield TimelineTab(self.project_dir)
            with TabPane("Log Explorer", id="tab-logs"):
                yield LogExplorerTab(self.project_dir)
            with TabPane("Data Lab", id="tab-datalab"):
                yield DataLabTab(self.project_dir)
            with TabPane("SemVer Lab", id="tab-semver"):
                yield SemVerTab()
            with TabPane("Logic Lab", id="tab-logic-lab"):
                yield LogicLabTab()
            with TabPane("Database", id="tab-database"):
                yield DatabaseTab(self.project_dir)
            with TabPane("DB Diagram", id="tab-db-diag"):
                yield DatabaseDiagramTab(self.project_dir)
            with TabPane("Secrets", id="tab-secrets"):
                yield SecretsTab(self.project_dir)
            with TabPane("Env", id="tab-env"):
                yield EnvTab(self.project_dir)
            with TabPane("API Lab", id="tab-api-lab"):
                yield ApiLabTab(self.project_dir)
            with TabPane("JWT Lab", id="tab-jwt"):
                yield JwtLabTab()
            with TabPane("Sanitizer", id="tab-sanitizer"):
                yield SanitizerTab(self.project_dir)
            with TabPane("Frontend", id="tab-frontend"):
                yield FrontendTab(self.project_dir)
            with TabPane("i18n", id="tab-i18n"):
                yield I18nTab(self.project_dir)
            with TabPane("Cost", id="tab-cost"):
                yield CostTab(self.project_dir)
            with TabPane("Playground", id="tab-playground"):
                yield PlaygroundTab(self.project_dir)
            with TabPane("Prompt Lab", id="tab-prompt-lab"):
                yield PromptLabTab(self.project_dir)
            with TabPane("Presentation", id="tab-presentation"):
                yield PresentationTab(self.project_dir)
            with TabPane("Quiz", id="tab-quiz"):
                yield QuizTab(self.project_dir)
            with TabPane("Regex Lab", id="tab-regex"):
                yield RegexLabTab(self.project_dir)
            with TabPane("Cron Lab", id="tab-cron"):
                yield CronLabTab(self.project_dir)
            with TabPane("Time Lab", id="tab-time"):
                yield TimeLabTab()
            with TabPane("Math Lab", id="tab-math"):
                yield MathLabTab()
            with TabPane("DevTools", id="tab-devtools"):
                yield DevToolsTab(self.project_dir)
            with TabPane("Hex Lab", id="tab-hex"):
                yield HexTab(self.project_dir)
            with TabPane("JSON Lab", id="tab-json"):
                yield JsonLabTab(self.project_dir)
            with TabPane("YAML Lab", id="tab-yaml"):
                yield YamlLabTab(self.project_dir)
            with TabPane("Markdown Lab", id="tab-markdown"):
                yield MarkdownLabTab(self.project_dir)
            with TabPane("CSV Lab", id="tab-csv"):
                yield CsvLabTab(self.project_dir)
            with TabPane("Diff Lab", id="tab-diff"):
                yield DiffLabTab(self.project_dir)
            with TabPane("Image Lab", id="tab-image"):
                yield ImageLabTab(self.project_dir)

            # Plugin Tabs
            for title, widget in self.plugin_manager.get_tui_tabs():
                safe_id = f"tab-plugin-{title.lower().replace(' ', '-')}"
                with TabPane(title, id=safe_id):
                    yield widget

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        # Handle dashboard buttons (bubble up)
        if event.button.id == "btn-refresh":
            self.action_refresh_dashboard()
        elif event.button.id == "btn-test":
            self.action_run_tests()
        elif event.button.id == "btn-lint":
            self.action_run_lint()

if __name__ == "__main__":
    # Add parent dir to path to allow direct execution
    import_path = str(Path(__file__).parent.parent)
    sys.path.append(import_path)

    project_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    app = AgentTUI(project_dir=project_path)
    app.run()
