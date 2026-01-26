import time
import subprocess
import shlex
from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Label, Button, DataTable, RichLog
from textual import on
from shared.scheduler import Scheduler, Task

class TUIScheduler(Scheduler):
    def __init__(self, project_dir: Path, log_widget: RichLog):
        super().__init__(project_dir)
        self.log_widget = log_widget

    def run_task(self, task: Task) -> None:
        def log(msg: str) -> None:
            if self.log_widget.app:
                self.log_widget.app.call_from_thread(self.log_widget.write, msg)
            else:
                self.log_widget.write(msg)

        log(f"\n[bold blue][Scheduler] Running: {task.name}[/bold blue]")
        # last_run is updated in tick() to prevent race conditions

        try:
            cmd_parts = shlex.split(task.command)
            # Use subprocess directly but capture output
            result = subprocess.run(
                cmd_parts,
                cwd=self.project_dir,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                log(f"[green]✅ {task.name} completed.[/green]")
                if result.stdout:
                    log(f"[dim]{result.stdout.strip()}[/dim]")
            else:
                log(f"[red]❌ {task.name} failed (exit code {result.returncode}).[/red]")
                if result.stderr:
                    log(f"[red]{result.stderr.strip()}[/red]")

        except Exception as e:
            log(f"[bold red]❌ Error executing {task.name}: {e}[/bold red]")

class SchedulerTab(Container):
    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.scheduler: TUIScheduler | None = None
        self.scheduler_active = False
        self.timer = None

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Autonomous Scheduler[/bold]", classes="welcome-text")

            with Horizontal(classes="stat-box"):
                yield Label("Status: [red]Stopped[/red]", id="lbl-sched-status")
                yield Button("Start", id="btn-sched-start", variant="success")
                yield Button("Stop", id="btn-sched-stop", variant="error", disabled=True)
                yield Button("Run Selected", id="btn-sched-run-now", variant="primary", disabled=True)
                yield Button("Refresh Config", id="btn-sched-refresh", variant="default")

            yield DataTable(id="sched-table")

            with VerticalScroll(classes="stat-box"):
                yield Label("[bold]Scheduler Log[/bold]")
                yield RichLog(id="sched-log", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        self.log_widget = self.query_one("#sched-log", RichLog)
        self.scheduler = TUIScheduler(self.project_dir, self.log_widget)

        table = self.query_one("#sched-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Task", "Interval", "Last Run", "Next Run", "Status")

        self.load_config()

    def load_config(self) -> None:
        if self.scheduler:
            self.scheduler.load_config()
            self.refresh_table()
            self.log_widget.write(f"Loaded {len(self.scheduler.tasks)} tasks.")

    def refresh_table(self) -> None:
        table = self.query_one("#sched-table", DataTable)
        table.clear()

        if not self.scheduler:
            return

        for task in self.scheduler.tasks:
            # Calculate Next Run
            if task.last_run == 0:
                status = "Pending"
                next_run = "Now"
                last_run = "Never"
            else:
                next_ts = task.last_run + task.interval
                wait = next_ts - time.time()
                if wait <= 0:
                    status = "Due"
                    next_run = "Now"
                else:
                    status = "Waiting"
                    # Format seconds to mm:ss or similar
                    if wait > 3600:
                        next_run = f"{wait/3600:.1f}h"
                    elif wait > 60:
                        next_run = f"{wait/60:.1f}m"
                    else:
                        next_run = f"{wait:.0f}s"

                # Format last run
                import datetime
                last_run = datetime.datetime.fromtimestamp(task.last_run).strftime("%H:%M:%S")

            interval_display = f"{task.interval}s"

            table.add_row(
                task.name,
                interval_display,
                last_run,
                next_run,
                status,
                key=task.name
            )

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-sched-start":
            self.start_scheduler()
        elif event.button.id == "btn-sched-stop":
            self.stop_scheduler()
        elif event.button.id == "btn-sched-run-now":
            await self.run_selected()
        elif event.button.id == "btn-sched-refresh":
            self.load_config()

    def start_scheduler(self) -> None:
        self.scheduler_active = True
        self.query_one("#lbl-sched-status", Label).update("Status: [green]Running[/green]")
        self.query_one("#btn-sched-start").disabled = True
        self.query_one("#btn-sched-stop").disabled = False

        # Start interval
        self.timer = self.set_interval(1.0, self.tick)
        self.log_widget.write("[green]Scheduler started.[/green]")

    def stop_scheduler(self) -> None:
        self.scheduler_active = False
        self.query_one("#lbl-sched-status", Label).update("Status: [red]Stopped[/red]")
        self.query_one("#btn-sched-start").disabled = False
        self.query_one("#btn-sched-stop").disabled = True

        if self.timer:
            self.timer.stop()
            self.timer = None
        self.log_widget.write("[red]Scheduler stopped.[/red]")

    def tick(self) -> None:
        if not self.scheduler:
            return

        for task in self.scheduler.tasks:
            if task.is_due():
                # Update last_run immediately to prevent double scheduling
                task.last_run = time.time()
                self.run_task_background(task)

        # Always refresh table to show countdowns
        self.refresh_table()

    @on(DataTable.RowSelected, "#sched-table")
    def on_task_selected(self) -> None:
        self.query_one("#btn-sched-run-now").disabled = False

    async def run_selected(self) -> None:
        table = self.query_one("#sched-table", DataTable)
        if table.cursor_row is None:
            return

        row = table.get_row_at(table.cursor_row)
        task_name = row[0]

        task = next((t for t in self.scheduler.tasks if t.name == task_name), None)
        if task:
            self.run_task_background(task)

    def run_task_background(self, task: Task) -> None:
        # Run in worker
        self.run_worker(self._do_run_task(task), exclusive=False)

    async def _do_run_task(self, task: Task) -> None:
        # We need to run the blocking call in a thread
        import asyncio

        # Because run_task updates the UI widget (RichLog), and we are in a thread,
        # we strictly should schedule the updates on the main thread.
        # But since TUIScheduler calls write() directly, let's update TUIScheduler to be safe
        # OR assume Textual handles it (it often does via event loop injection).
        # To be strictly correct:

        await asyncio.to_thread(self.scheduler.run_task, task)
        # Update table after run
        self.call_after_refresh(self.refresh_table)
