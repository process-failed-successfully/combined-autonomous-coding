import asyncio
from datetime import datetime
from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Label, Button, Select, DataTable, Input
from textual import on
from shared.productivity_lab import ProductivityManager
from shared.task_manager import TaskManager


class ProductivityTab(Container):
    """
    Productivity Dashboard with Pomodoro Timer.
    """

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = ProductivityManager(project_dir)
        self.task_manager = TaskManager(project_dir)
        self.timer = None
        self.remaining_seconds = 25 * 60  # Default 25 min
        self.initial_duration = 25 * 60
        self.timer_active = False

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Label("[bold]Focus & Productivity[/bold]", classes="welcome-text")

            # Timer Section
            with Container(classes="stat-box", id="prod-timer-container"):
                yield Label("25:00", id="lbl-timer-display", classes="timer-display")

                # Progress Bar (ASCII)
                yield Label("[--------------------]", id="lbl-timer-progress")

                yield Label("Select Task:")
                yield Select([], id="sel-prod-task", prompt="Pick a task or Free Focus")

                with Horizontal(classes="timer-controls"):
                    yield Input(value="25", id="input-prod-focus-min", placeholder="Focus min", classes="timer-input")
                    yield Button("Start Focus", id="btn-prod-start-focus", variant="success")
                    yield Input(value="5", id="input-prod-break-min", placeholder="Break min", classes="timer-input")
                    yield Button("Start Break", id="btn-prod-start-break", variant="primary")
                    yield Button("Stop", id="btn-prod-stop", variant="error", disabled=True)

            # Quick Actions
            with Horizontal(classes="stat-box"):
                yield Input(placeholder="Log a distraction...", id="input-prod-distraction")
                yield Button("Log Distraction", id="btn-prod-log-distraction", variant="warning")

            # Stats Section
            with Container(classes="stat-box"):
                yield Label("[bold]Today's Stats[/bold]")
                with Horizontal():
                    with Vertical():
                        yield Label("Focus Time", classes="stat-label")
                        yield Label("0m", id="lbl-stat-focus", classes="stat-value")
                    with Vertical():
                        yield Label("Breaks", classes="stat-label")
                        yield Label("0m", id="lbl-stat-break", classes="stat-value")
                    with Vertical():
                        yield Label("Sessions", classes="stat-label")
                        yield Label("0", id="lbl-stat-sessions", classes="stat-value")
                    with Vertical():
                        yield Label("Distractions", classes="stat-label")
                        yield Label("0", id="lbl-stat-distractions", classes="stat-value")

            # History
            with Container(classes="stat-box"):
                yield Label("[bold]Session History[/bold]")
                yield DataTable(id="prod-history-table")

    def on_mount(self) -> None:
        # Load tasks
        self.load_tasks()

        # Init Table
        table = self.query_one("#prod-history-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Time", "Type", "Duration", "Task")

        self.update_stats()
        self.update_history()

    def load_tasks(self) -> None:
        # Run in thread if it's slow? TaskManager fetches from network.
        # But for mount we can try sync first or schedule async.
        # Let's use call_later or just run it. Fetching might block.
        # I'll populate with local TODOs quickly or just empty list then async load.

        self.query_one("#sel-prod-task", Select).set_options([("Free Focus", "free_focus")])
        self.query_one("#sel-prod-task", Select).value = "free_focus"

        asyncio.create_task(self._async_load_tasks())

    async def _async_load_tasks(self) -> None:
        try:
            tasks = await asyncio.to_thread(self.task_manager.fetch_all_tasks)
            options = []
            options.append(("Free Focus", "free_focus"))

            for t in tasks:
                label = f"[{t.source.upper()}] {t.title[:40]}"
                options.append((label, t.id))

            # Select.set_options replaces options
            self.query_one("#sel-prod-task", Select).set_options(options)
            # Restore value if possible or default
            self.query_one("#sel-prod-task", Select).value = "free_focus"
        except Exception:
            pass

    def update_stats(self) -> None:
        stats = self.manager.get_today_stats()

        focus_min = int(stats["work_time"] // 60)
        break_min = int(stats["break_time"] // 60)

        self.query_one("#lbl-stat-focus", Label).update(f"{focus_min}m")
        self.query_one("#lbl-stat-break", Label).update(f"{break_min}m")
        self.query_one("#lbl-stat-sessions", Label).update(str(stats["sessions_count"]))
        self.query_one("#lbl-stat-distractions", Label).update(str(stats["distractions"]))

    def update_history(self) -> None:
        table = self.query_one("#prod-history-table", DataTable)
        table.clear()

        # Show last 10 sessions reversed
        for s in reversed(self.manager.sessions[-10:]):
            start_str = datetime.fromtimestamp(s.start_time).strftime("%H:%M")
            dur_str = f"{int(s.duration // 60)}m {int(s.duration % 60)}s"
            task_str = s.task_id if s.task_id else "-"

            # Color code
            type_fmt = f"[green]{s.type.upper()}[/green]" if s.type == "work" else f"[blue]{s.type.upper()}[/blue]"

            table.add_row(start_str, type_fmt, dur_str, task_str)

    @on(Button.Pressed, "#btn-prod-start-focus")
    def on_start_focus(self) -> None:
        try:
            minutes = int(self.query_one("#input-prod-focus-min", Input).value)
        except ValueError:
            minutes = 25
        self.start_timer(minutes * 60, "work")

    @on(Button.Pressed, "#btn-prod-start-break")
    def on_start_break(self) -> None:
        try:
            minutes = int(self.query_one("#input-prod-break-min", Input).value)
        except ValueError:
            minutes = 5
        self.start_timer(minutes * 60, "break")

    @on(Button.Pressed, "#btn-prod-stop")
    def on_stop(self) -> None:
        self.stop_timer()

    @on(Button.Pressed, "#btn-prod-log-distraction")
    def on_log_distraction(self) -> None:
        inp = self.query_one("#input-prod-distraction", Input)
        val = inp.value
        if val:
            self.manager.log_distraction(val)
            self.notify("Distraction logged.")
            inp.value = ""
            self.update_stats()

    def start_timer(self, duration: int, session_type: str) -> None:
        task_id = self.query_one("#sel-prod-task", Select).value

        self.manager.start_session(session_type, task_id)
        self.remaining_seconds = duration
        self.initial_duration = duration  # Store for progress bar
        self.timer_active = True

        self.query_one("#btn-prod-start-focus").disabled = True
        self.query_one("#btn-prod-start-break").disabled = True
        self.query_one("#btn-prod-stop").disabled = False

        # Start tick
        if not self.timer:
            self.timer = self.set_interval(1.0, self.tick)

    def stop_timer(self) -> None:
        self.timer_active = False
        self.manager.stop_session()

        if self.timer:
            self.timer.stop()
            self.timer = None

        self.query_one("#btn-prod-start-focus").disabled = False
        self.query_one("#btn-prod-start-break").disabled = False
        self.query_one("#btn-prod-stop").disabled = True

        self.query_one("#lbl-timer-display", Label).update("00:00")
        self.query_one("#lbl-timer-progress", Label).update("[--------------------]")

        self.update_stats()
        self.update_history()
        self.notify("Session stopped.")

    def tick(self) -> None:
        if not self.timer_active:
            return

        self.remaining_seconds -= 1

        # Update Display
        m = self.remaining_seconds // 60
        s = self.remaining_seconds % 60
        self.query_one("#lbl-timer-display", Label).update(f"{m:02d}:{s:02d}")

        # Update Progress
        pct = 1.0 - (self.remaining_seconds / self.initial_duration)
        bars = int(20 * pct)
        progress = "█" * bars + "-" * (20 - bars)

        # Color based on phase
        color = "green"
        if pct > 0.8:
            color = "yellow"
        if pct > 0.95:
            color = "red"

        self.query_one("#lbl-timer-progress", Label).update(f"[{color}][{progress}][/{color}]")

        # Update stats live (to show accumulating time)
        self.update_stats()

        if self.remaining_seconds <= 0:
            self.stop_timer()
            self.notify("Timer finished!", severity="information")
            self.app.bell()
