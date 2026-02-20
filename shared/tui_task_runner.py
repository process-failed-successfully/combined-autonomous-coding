from pathlib import Path
import asyncio
from textual.app import ComposeResult
from textual.widgets import Label, Button, DataTable, RichLog, Input
from textual.containers import Container, Horizontal, Vertical
from textual import on

from shared.task_runner_lab import TaskRunnerManager, Task

class TaskRunnerTab(Container):
    """Tab for running project tasks."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = TaskRunnerManager(project_dir)
        self.selected_task: Task | None = None
        self.task_running = False

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: Task List
            with Vertical(id="runner-list-container", classes="stat-box"):
                yield Label("[bold]Available Tasks[/bold]")
                yield Input(placeholder="Filter tasks...", id="runner-filter")
                yield DataTable(id="runner-table")
                yield Button("Refresh", id="btn-runner-refresh", variant="default")

            # Right Pane: Output
            with Vertical(id="runner-output-container"):
                yield Label("[bold]Task Output[/bold]", id="runner-header")

                with Horizontal(id="runner-actions", classes="stat-box"):
                    yield Button("Run Task", id="btn-runner-run", variant="success", disabled=True)
                    yield Button("Stop", id="btn-runner-stop", variant="error", disabled=True)
                    yield Button("Clear Log", id="btn-runner-clear", variant="default")

                yield RichLog(id="runner-log", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        table = self.query_one("#runner-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Source", "Name", "Command")
        self.load_tasks()

    def load_tasks(self) -> None:
        table = self.query_one("#runner-table", DataTable)
        table.clear()

        self.tasks_cache: list[Task] = self.manager.list_tasks()
        self._update_table()

    def _update_table(self) -> None:
        table = self.query_one("#runner-table", DataTable)
        table.clear()

        filter_text = self.query_one("#runner-filter", Input).value.lower()

        for i, task in enumerate(self.tasks_cache):
            if filter_text and filter_text not in task.name.lower() and filter_text not in task.command.lower():
                continue

            table.add_row(
                task.source,
                task.name,
                task.command,
                key=str(i) # Store index as key
            )

    @on(Input.Changed, "#runner-filter")
    def on_filter_changed(self) -> None:
        self._update_table()

    @on(Button.Pressed, "#btn-runner-refresh")
    def on_refresh(self) -> None:
        self.load_tasks()
        self.notify("Tasks refreshed.")

    @on(DataTable.RowSelected, "#runner-table")
    def on_task_selected(self, event: DataTable.RowSelected) -> None:
        index = int(event.row_key.value)
        self.selected_task = self.tasks_cache[index]

        self.query_one("#runner-header").update(f"[bold]Task: {self.selected_task.name}[/bold]")
        self.query_one("#btn-runner-run").disabled = False
        self.query_one("#btn-runner-run").label = f"Run {self.selected_task.name}"

    @on(Button.Pressed, "#btn-runner-clear")
    def on_clear(self) -> None:
        self.query_one("#runner-log", RichLog).clear()

    @on(Button.Pressed, "#btn-runner-run")
    async def on_run(self) -> None:
        if not self.selected_task:
            return

        self.task_running = True
        self.query_one("#btn-runner-run").disabled = True
        self.query_one("#btn-runner-stop").disabled = False

        log = self.query_one("#runner-log", RichLog)
        log.write(f"[bold green]Starting task: {self.selected_task.name}[/bold green]")
        log.write(f"Command: {self.selected_task.command}")
        log.write("-" * 40)

        # Run in thread
        import asyncio

        # Helper to push to log from thread
        def on_output(line):
            self.app.call_from_thread(log.write, line)

        try:
            returncode = await asyncio.to_thread(
                self.manager.run_task,
                self.selected_task,
                on_output=on_output
            )

            if returncode == 0:
                log.write(f"\n[bold green]Task finished successfully (exit code 0).[/bold green]")
                self.notify("Task finished successfully.")
            else:
                log.write(f"\n[bold red]Task finished with error (exit code {returncode}).[/bold red]")
                self.notify("Task failed.", severity="error")

        except Exception as e:
            log.write(f"\n[bold red]Execution error: {e}[/bold red]")
            self.notify(f"Error: {e}", severity="error")

        finally:
            self.task_running = False
            self.query_one("#btn-runner-run").disabled = False
            self.query_one("#btn-runner-stop").disabled = True

    @on(Button.Pressed, "#btn-runner-stop")
    def on_stop(self) -> None:
        # TODO: Implement stop logic in Manager (needs storing process handle)
        # For now, just notify
        self.notify("Stop not implemented yet (requires process management).", severity="warning")
