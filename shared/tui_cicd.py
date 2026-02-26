from typing import Optional
from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, DataTable, Label, Input, RichLog, ListItem, ListView
from textual import on
from shared.cicd_lab import CicdLabManager
import asyncio

class CicdLabTab(Container):
    """Tab for managing GitHub Actions CI/CD workflows."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = CicdLabManager(project_dir)
        self.selected_workflow_id = None
        self.selected_workflow_path = None
        self.selected_run_id = None

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]CI/CD Lab - GitHub Actions[/bold]", classes="welcome-text")

            with Horizontal():
                # Left Pane: Workflows
                with Vertical(id="cicd-workflows-container", classes="stat-box"):
                    yield Label("[bold]Workflows[/bold]")
                    yield Button("Refresh", id="btn-cicd-refresh", variant="default")
                    yield ListView(id="cicd-workflow-list")

                # Center Pane: Runs & Trigger
                with Vertical(id="cicd-runs-container"):
                    with Horizontal(classes="stat-box"):
                        yield Label("Selected Workflow:", id="lbl-cicd-workflow-name")
                        yield Button("Trigger Run", id="btn-cicd-trigger", variant="primary", disabled=True)
                        yield Input(placeholder="Branch/Ref (default: main)", id="inp-cicd-ref", value="main")

                    yield Label("[bold]Recent Runs[/bold]")
                    yield DataTable(id="cicd-runs-table")

                # Right Pane: Job Details
                with Vertical(id="cicd-jobs-container", classes="stat-box"):
                    yield Label("[bold]Job Details[/bold]")
                    yield RichLog(id="cicd-jobs-log", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        table = self.query_one("#cicd-runs-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("ID", "Status", "Branch", "Commit", "Duration")
        self.load_workflows()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cicd-refresh":
            self.load_workflows()
            if self.selected_workflow_id:
                self.load_runs(self.selected_workflow_id)
        elif event.button.id == "btn-cicd-trigger":
            await self.trigger_workflow()

    def load_workflows(self) -> None:
        # Fire and forget async task
        asyncio.create_task(self._load_workflows_async())

    async def _load_workflows_async(self) -> None:
        list_view = self.query_one("#cicd-workflow-list", ListView)
        # We can't easily clear/append safely from thread, but we are in async loop here.
        # But list_workflows is blocking, so we run it in thread.

        try:
            workflows = await asyncio.to_thread(self.manager.list_workflows)

            list_view.clear()

            if not workflows:
                self.notify("No workflows found.", severity="warning")
                return

            if "error" in workflows[0]:
                self.notify(f"Error loading workflows: {workflows[0]['error']}", severity="error")
                return

            for wf in workflows:
                name = wf.get("name", "Unknown")
                state = wf.get("state", "active")
                color = "green" if state == "active" else "red"
                label = f"[{color}]●[/] {name}"

                item = ListItem(Label(label, markup=True))
                item.workflow_id = wf.get("id")
                item.workflow_name = name
                item.workflow_path = wf.get("path") # e.g. .github/workflows/main.yml
                list_view.append(item)

        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    @on(ListView.Selected, "#cicd-workflow-list")
    def on_workflow_selected(self, event: ListView.Selected) -> None:
        if hasattr(event.item, "workflow_id"):
            self.selected_workflow_id = event.item.workflow_id
            self.selected_workflow_path = event.item.workflow_path
            name = event.item.workflow_name

            self.query_one("#lbl-cicd-workflow-name", Label).update(f"Selected: [bold]{name}[/bold]")
            self.query_one("#btn-cicd-trigger").disabled = False
            self.load_runs(self.selected_workflow_id)

    def load_runs(self, workflow_id: int) -> None:
        asyncio.create_task(self._load_runs_async(workflow_id))

    async def _load_runs_async(self, workflow_id: int) -> None:
        table = self.query_one("#cicd-runs-table", DataTable)
        table.clear()
        self.query_one("#cicd-jobs-log", RichLog).clear()

        try:
            runs = await asyncio.to_thread(self.manager.list_runs, workflow_id)

            if runs and "error" in runs[0]:
                self.notify(f"Error loading runs: {runs[0]['error']}", severity="error")
                return

            for run in runs:
                status = run.get("status", "unknown")
                conclusion = run.get("conclusion", "")

                # Composite status
                display_status = status
                if conclusion:
                    display_status = conclusion

                # Colorize
                if display_status == "success":
                    display_status = "[green]success[/green]"
                elif display_status == "failure":
                    display_status = "[red]failure[/red]"
                elif display_status == "in_progress":
                    display_status = "[yellow]running[/yellow]"

                # Calculate duration if possible, or just updated_at
                updated = run.get("updated_at", "")

                table.add_row(
                    str(run.get("id")),
                    display_status,
                    run.get("head_branch", ""),
                    run.get("head_sha", "")[:7],
                    updated,
                    key=str(run.get("id"))
                )

        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    @on(DataTable.RowSelected, "#cicd-runs-table")
    def on_run_selected(self, event: DataTable.RowSelected) -> None:
        run_id = int(event.row_key.value)
        self.selected_run_id = run_id
        self.load_run_details(run_id)

    def load_run_details(self, run_id: int) -> None:
        asyncio.create_task(self._load_run_details_async(run_id))

    async def _load_run_details_async(self, run_id: int) -> None:
        log = self.query_one("#cicd-jobs-log", RichLog)
        log.clear()
        log.write(f"Loading jobs for run {run_id}...")

        try:
            jobs = await asyncio.to_thread(self.manager.get_run_jobs, run_id)
            log.clear()

            if jobs and "error" in jobs[0]:
                log.write(f"[red]Error: {jobs[0]['error']}[/red]")
                return

            for job in jobs:
                name = job.get("name", "Unknown")
                status = job.get("status", "")
                conclusion = job.get("conclusion", "")

                color = "white"
                if conclusion == "success": color = "green"
                elif conclusion == "failure": color = "red"
                elif status == "in_progress": color = "yellow"

                log.write(f"[bold {color}]{name}[/]")
                log.write(f"  Status: {status} / {conclusion}")

                steps = job.get("steps", [])
                for step in steps:
                    s_name = step.get("name", "Step")
                    s_conc = step.get("conclusion", "pending")
                    s_color = "dim"
                    if s_conc == "failure": s_color = "red"
                    elif s_conc == "success": s_color = "green"

                    log.write(f"    - [{s_color}]{s_name}[/] ({s_conc})")
                log.write("")

        except Exception as e:
            log.write(f"[red]Error: {e}[/red]")

    async def trigger_workflow(self) -> None:
        if not self.selected_workflow_id:
            return

        ref = self.query_one("#inp-cicd-ref", Input).value

        # Check for inputs (sync file read is fast enough usually, but strictly should be async too)
        # manager.get_workflow_inputs is fast (local file read).
        inputs = {}
        if self.selected_workflow_path:
            wf_inputs = self.manager.get_workflow_inputs(self.selected_workflow_path)
            if wf_inputs:
                pass

        self.notify(f"Triggering workflow {self.selected_workflow_id} on {ref}...")

        try:
            success = await asyncio.to_thread(self.manager.trigger_workflow, self.selected_workflow_id, ref, inputs)
            if success:
                self.notify("Workflow triggered successfully.")
                # Refresh runs after a short delay
                await asyncio.sleep(2)
                self.load_runs(self.selected_workflow_id)
            else:
                self.notify("Failed to trigger workflow.", severity="error")
        except Exception as e:
            self.notify(f"Error triggering workflow: {e}", severity="error")
