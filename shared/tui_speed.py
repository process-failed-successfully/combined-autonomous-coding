from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, Input, RichLog
from textual import on, work
import contextlib

from shared.speed_lab import SpeedLabManager


class TUIStream:
    """Helper to redirect stdout to a RichLog widget in a thread-safe way."""
    def __init__(self, log_widget, app):
        self.log = log_widget
        self.app = app

    def write(self, text):
        # We might receive partial writes, but for log we usually want lines.
        # RichLog.write adds a newline by default.
        if text.strip():
            self.app.call_from_thread(self.log.write, text.rstrip())

    def flush(self):
        pass


class SpeedLabTab(Container):
    """Tab for Speed Lab Benchmarks."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = SpeedLabManager()

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: Controls
            with Vertical(classes="stat-box", id="speed-controls"):
                yield Label("[bold]Benchmarks[/bold]")
                yield Button("Internet Speed", id="btn-speed-internet", variant="primary")
                yield Button("Disk I/O", id="btn-speed-disk", variant="primary")
                yield Button("CPU Benchmark", id="btn-speed-cpu", variant="primary")
                yield Button("Memory Benchmark", id="btn-speed-memory", variant="primary")

                yield Label("[bold]Configuration[/bold]", classes="mt-2")
                yield Label("Size (MB) / Limit:")
                yield Input(placeholder="100", id="speed-size", value="100")
                yield Label("Duration (s) / Timeout:")
                yield Input(placeholder="10", id="speed-duration", value="30")

            # Right Pane: Output
            with Vertical(id="speed-output-container"):
                yield Label("[bold]Output[/bold]")
                yield RichLog(id="speed-log", wrap=True, highlight=True, markup=True)

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-speed-internet":
            self.run_internet_test()
        elif event.button.id == "btn-speed-disk":
            self.run_disk_test()
        elif event.button.id == "btn-speed-cpu":
            self.run_cpu_test()
        elif event.button.id == "btn-speed-memory":
            self.run_memory_test()

    def _get_int_input(self, input_id: str, default: int) -> int:
        val = self.query_one(f"#{input_id}", Input).value
        try:
            return int(val)
        except ValueError:
            return default

    @work(thread=True)
    def run_internet_test(self) -> None:
        log = self.query_one("#speed-log", RichLog)
        timeout = self._get_int_input("speed-duration", 30)

        self.app.call_from_thread(log.write, "[bold cyan]Running Internet Speed Test...[/bold cyan]")

        stream = TUIStream(log, self.app)
        with contextlib.redirect_stdout(stream):
            try:
                self.manager.check_internet_speed(timeout=timeout)
            except Exception as e:
                print(f"Error: {e}")

        self.app.call_from_thread(log.write, "[bold green]Done.[/bold green]")

    @work(thread=True)
    def run_disk_test(self) -> None:
        log = self.query_one("#speed-log", RichLog)
        size = self._get_int_input("speed-size", 100)

        self.app.call_from_thread(log.write, f"[bold cyan]Running Disk Benchmark ({size} MB)...[/bold cyan]")

        stream = TUIStream(log, self.app)
        with contextlib.redirect_stdout(stream):
            try:
                self.manager.check_disk_speed(size_mb=size, path=str(self.project_dir))
            except Exception as e:
                print(f"Error: {e}")

        self.app.call_from_thread(log.write, "[bold green]Done.[/bold green]")

    @work(thread=True)
    def run_cpu_test(self) -> None:
        log = self.query_one("#speed-log", RichLog)
        limit = self._get_int_input("speed-size", 20000)  # Reusing size input for limit

        self.app.call_from_thread(log.write, f"[bold cyan]Running CPU Benchmark (Limit: {limit})...[/bold cyan]")

        stream = TUIStream(log, self.app)
        with contextlib.redirect_stdout(stream):
            try:
                self.manager.check_cpu_speed(limit=limit)
            except Exception as e:
                print(f"Error: {e}")

        self.app.call_from_thread(log.write, "[bold green]Done.[/bold green]")

    @work(thread=True)
    def run_memory_test(self) -> None:
        log = self.query_one("#speed-log", RichLog)
        size = self._get_int_input("speed-size", 100)

        self.app.call_from_thread(log.write, f"[bold cyan]Running Memory Benchmark ({size} MB)...[/bold cyan]")

        stream = TUIStream(log, self.app)
        with contextlib.redirect_stdout(stream):
            try:
                self.manager.check_memory_speed(size_mb=size)
            except Exception as e:
                print(f"Error: {e}")

        self.app.call_from_thread(log.write, "[bold green]Done.[/bold green]")
