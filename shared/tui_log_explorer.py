from pathlib import Path
from typing import List, Optional
from textual.app import ComposeResult
from textual.widgets import Label, Button, ListView, ListItem, RichLog, DataTable, Input, Markdown
from textual.containers import Container, Horizontal, Vertical
from textual import on
from shared.cli_utils import get_all_log_files
from shared.log_explorer import LogParser, AgentStep
from shared.ask import run_ask_logic
import io
import contextlib

class LogListItem(ListItem):
    """Custom ListItem that holds the log path."""
    def __init__(self, label: Label, log_path: Path) -> None:
        super().__init__(label)
        self.log_path = log_path

class LogExplorerTab(Container):
    """Tab for exploring agent execution logs."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.parser = LogParser()
        self.current_log_path: Optional[Path] = None
        self.current_steps: List[AgentStep] = []

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left: Run Selector
            with Vertical(id="log-sidebar", classes="stat-box"):
                yield Label("[bold]Agent Runs[/bold]")
                yield ListView(id="log-run-list")
                yield Button("Refresh", id="btn-log-refresh", variant="default")

            # Middle: Timeline
            with Vertical(id="log-timeline-container", classes="stat-box"):
                yield Label("[bold]Execution Timeline[/bold]")
                yield DataTable(id="log-step-table")

            # Right: Details
            with Vertical(id="log-details-container"):
                yield Label("[bold]Step Details[/bold]")
                yield RichLog(id="log-details-view", wrap=True, highlight=True, markup=True)

                with Horizontal(classes="stat-box"):
                    yield Button("Analyze Run (AI)", id="btn-log-analyze", variant="warning", disabled=True)

    def on_mount(self) -> None:
        # Setup DataTable
        table = self.query_one("#log-step-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Time", "Type", "Description")

        self.load_runs()

    def load_runs(self) -> None:
        run_list = self.query_one("#log-run-list", ListView)
        run_list.clear()

        logs = get_all_log_files()
        if not logs:
            run_list.append(ListItem(Label("No logs found")))
            return

        for log_file in logs:
            try:
                size = log_file.stat().st_size
                size_str = f"{size / 1024:.1f} KB"
                label = f"{log_file.name} ({size_str})"
            except OSError:
                label = log_file.name

            item = LogListItem(Label(label), log_file)
            run_list.append(item)

        # Select first by default
        if run_list.children:
            run_list.index = 0
            # Manually trigger load
            first_item = run_list.children[0]
            if isinstance(first_item, LogListItem):
                self.load_run(first_item.log_path)

    @on(ListView.Selected, "#log-run-list")
    def on_run_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, LogListItem):
            self.load_run(event.item.log_path)

    def load_run(self, log_path: Path) -> None:
        self.current_log_path = log_path
        self.query_one("#btn-log-analyze").disabled = False

        table = self.query_one("#log-step-table", DataTable)
        table.clear()
        self.query_one("#log-details-view", RichLog).clear()

        self.current_steps = self.parser.parse_run(log_path)

        if not self.current_steps:
            return

        for step in self.current_steps:
            # Color code type
            type_fmt = step.type
            if step.type == "ERROR":
                type_fmt = f"[red]{step.type}[/red]"
            elif step.type == "THOUGHT":
                type_fmt = f"[blue]{step.type}[/blue]"
            elif step.type == "ACTION":
                type_fmt = f"[green]{step.type}[/green]"
            elif step.type == "OUTPUT":
                type_fmt = f"[yellow]{step.type}[/yellow]"

            table.add_row(
                step.timestamp,
                type_fmt,
                step.description,
                key=str(step.step_id)
            )

    @on(DataTable.RowSelected, "#log-step-table")
    def on_step_selected(self, event: DataTable.RowSelected) -> None:
        if event.row_key.value is None:
            return
        step_id = int(event.row_key.value)
        step = next((s for s in self.current_steps if s.step_id == step_id), None)

        view = self.query_one("#log-details-view", RichLog)
        view.clear()

        if step:
            view.write(f"[bold]Timestamp:[/bold] {step.timestamp}")
            view.write(f"[bold]Type:[/bold] {step.type}")
            view.write(f"[bold]Description:[/bold] {step.description}")
            view.write("\n[bold]Content:[/bold]")
            view.write(step.details)

    @on(Button.Pressed, "#btn-log-refresh")
    def on_refresh(self) -> None:
        self.load_runs()
        self.notify("Logs refreshed.")

    @on(Button.Pressed, "#btn-log-analyze")
    async def on_analyze(self) -> None:
        if not self.current_log_path:
            return

        view = self.query_one("#log-details-view", RichLog)
        view.clear()
        view.write("[bold italic]Analyzing run with AI...[/bold italic]")
        self.notify("Analyzing run...", severity="information")

        # Capture stdout from run_ask_logic
        capture = io.StringIO()

        # Prompt
        steps_summary = "\n".join([f"{s.timestamp} - {s.type} - {s.description}" for s in self.current_steps[:100]])
        prompt = f"Analyze this agent run summary. Identify specific errors or loops. Suggest fixes.\n\n{steps_summary}"

        success = False
        import asyncio
        try:
            with contextlib.redirect_stdout(capture):
                success = await run_ask_logic(
                    query=prompt,
                    project_dir=self.project_dir,
                    agent_type="gemini", # Default to gemini or make selectable
                    verbose=False
                )
        except Exception as e:
            capture.write(f"Error: {e}")

        result = capture.getvalue()

        view.clear()
        view.write("[bold]AI Analysis Result:[/bold]\n")
        if success:
            view.write(result)
        else:
            view.write(f"[red]{result}[/red]")
