from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Label, DataTable, Button, RichLog
from textual.containers import Container, Horizontal, Vertical
from textual import on
from shared.proc_lab import ProcLabManager
import asyncio

class ProcLabTab(Container):
    """Tab for managing Procfile processes."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = ProcLabManager(project_dir)
        self.selected_process = None
        self.proc_map = {} # name -> command

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: Process List
            with Vertical(id="proc-list-container", classes="stat-box"):
                yield Label("[bold]Processes[/bold]")
                yield DataTable(id="proc-table")

                with Horizontal():
                    yield Button("Start All", id="btn-proc-start-all", variant="success")
                    yield Button("Stop All", id="btn-proc-stop-all", variant="error")

                yield Button("Refresh", id="btn-proc-refresh", variant="default")

            # Right Pane: Logs & Controls
            with Vertical(id="proc-details-container"):
                with Horizontal(classes="stat-box", id="proc-controls"):
                    yield Label("Select a process...", id="proc-header")
                    yield Button("Start", id="btn-proc-start", variant="success", disabled=True)
                    yield Button("Stop", id="btn-proc-stop", variant="error", disabled=True)
                    yield Button("Restart", id="btn-proc-restart", variant="warning", disabled=True)
                    yield Button("Clear Logs", id="btn-proc-clear", variant="default")

                yield RichLog(id="proc-log", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        table = self.query_one("#proc-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Name", "Status", "PID")
        self.load_processes()

    def on_unmount(self) -> None:
        # cleanup processes on exit
        asyncio.create_task(self.manager.stop_all())

    def load_processes(self) -> None:
        table = self.query_one("#proc-table", DataTable)
        table.clear()

        try:
            self.proc_map = self.manager.parse_procfile(self.project_dir / "Procfile")
        except FileNotFoundError:
            self.notify("Procfile not found.", severity="warning")
            return

        for name, cmd in self.proc_map.items():
            status = "[red]Stopped[/red]"
            pid = "-"

            proc = self.manager.processes.get(name)
            if proc and proc.returncode is None:
                status = "[green]Running[/green]"
                pid = str(proc.pid)

            table.add_row(name, status, pid, key=name)

    @on(DataTable.RowSelected, "#proc-table")
    def on_process_selected(self, event: DataTable.RowSelected) -> None:
        name = event.row_key.value
        self.selected_process = name
        self.update_header()
        self.update_buttons()

    def update_header(self) -> None:
        if self.selected_process:
            self.query_one("#proc-header", Label).update(f"[bold]{self.selected_process}[/bold]")
        else:
            self.query_one("#proc-header", Label).update("Select a process...")

    def update_buttons(self) -> None:
        if not self.selected_process:
            self.query_one("#btn-proc-start").disabled = True
            self.query_one("#btn-proc-stop").disabled = True
            self.query_one("#btn-proc-restart").disabled = True
            return

        proc = self.manager.processes.get(self.selected_process)
        is_running = proc and proc.returncode is None

        self.query_one("#btn-proc-start").disabled = is_running
        self.query_one("#btn-proc-stop").disabled = not is_running
        self.query_one("#btn-proc-restart").disabled = not is_running

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-proc-refresh":
            self.load_processes()
            self.update_buttons()
        elif event.button.id == "btn-proc-clear":
            self.query_one("#proc-log", RichLog).clear()
        elif event.button.id == "btn-proc-start":
            await self.start_selected()
        elif event.button.id == "btn-proc-stop":
            await self.stop_selected()
        elif event.button.id == "btn-proc-restart":
            await self.restart_selected()
        elif event.button.id == "btn-proc-start-all":
            await self.start_all()
        elif event.button.id == "btn-proc-stop-all":
            await self.stop_all()

    def log_callback(self, name: str, line: str) -> None:
        """Callback for log streaming. Uses call_from_thread for thread safety."""
        log = self.query_one("#proc-log", RichLog)

        # Color coding based on process name hash to make it distinct
        colors = ["green", "yellow", "blue", "magenta", "cyan"]
        color = colors[hash(name) % len(colors)]

        msg = f"[{color}][{name}][/{color}] {line}"
        self.app.call_from_thread(log.write, msg)

    async def start_selected(self) -> None:
        if not self.selected_process:
            return

        cmd = self.proc_map.get(self.selected_process)
        if not cmd:
            self.notify("Command not found.", severity="error")
            return

        self.notify(f"Starting {self.selected_process}...")
        success = await self.manager.start_process(self.selected_process, cmd, self.log_callback)

        if success:
            self.notify(f"Started {self.selected_process}.")
        else:
            self.notify(f"Failed to start {self.selected_process}.", severity="error")

        self.load_processes()
        self.update_buttons()

    async def stop_selected(self) -> None:
        if not self.selected_process:
            return

        self.notify(f"Stopping {self.selected_process}...")
        success = await self.manager.stop_process(self.selected_process)

        if success:
            self.notify(f"Stopped {self.selected_process}.")
        else:
            self.notify(f"Failed to stop {self.selected_process}.", severity="error")

        self.load_processes()
        self.update_buttons()

    async def restart_selected(self) -> None:
        await self.stop_selected()
        await self.start_selected()

    async def start_all(self) -> None:
        self.notify("Starting all processes...")
        for name, cmd in self.proc_map.items():
            await self.manager.start_process(name, cmd, self.log_callback)
        self.load_processes()
        self.update_buttons()

    async def stop_all(self) -> None:
        self.notify("Stopping all processes...")
        await self.manager.stop_all()
        self.load_processes()
        self.update_buttons()
