from pathlib import Path
from collections import deque
from textual.app import ComposeResult
from textual.widgets import Button, Label, RichLog, DataTable
from textual.containers import Container, Horizontal, Vertical
from textual import on

from shared.proc_lab import ProcLabManager

class ProcLabTab(Container):
    """Tab for managing Procfile processes."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = ProcLabManager(project_dir)
        self.selected_process = None
        self.output_buffers = {}  # name -> deque
        self.procfile_path = self.project_dir / "Procfile"

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: Process List
            with Vertical(id="proc-list-container", classes="stat-box"):
                yield Label("[bold]Processes[/bold]")
                yield DataTable(id="proc-table")

                with Horizontal():
                    yield Button("Refresh", id="btn-proc-refresh", variant="default")
                    yield Button("Stop All", id="btn-proc-stop-all", variant="error")

            # Right Pane: Details & Logs
            with Vertical(id="proc-details-container"):
                yield Label("[bold]Process Output[/bold]", id="proc-header")
                yield RichLog(id="proc-log", wrap=True, highlight=True, markup=True)

                with Horizontal(id="proc-actions"):
                    yield Button("Start", id="btn-proc-start", variant="success", disabled=True)
                    yield Button("Stop", id="btn-proc-stop", variant="error", disabled=True)
                    yield Button("Clear Logs", id="btn-proc-clear", variant="default", disabled=True)

    def on_mount(self) -> None:
        # Check if Procfile exists
        if not self.procfile_path.exists():
            self.notify("Procfile not found.", severity="warning")

        # Load config
        try:
            self.manager.load_config(self.procfile_path)
        except FileNotFoundError:
            pass

        table = self.query_one("#proc-table", DataTable)
        table.cursor_type = "row"
        table.add_column("Name", key="name")
        table.add_column("Status", key="status")
        table.add_column("PID", key="pid")

        self.refresh_table()

        # Start a UI update timer? Or just rely on events.
        # Status updates (PID/Running) might change.
        self.refresh_timer = self.set_interval(1.0, self.refresh_table)

    def on_unmount(self) -> None:
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()

    def refresh_table(self) -> None:
        try:
            table = self.query_one("#proc-table", DataTable)
        except Exception:
            # Widget might be unmounting
            return

        # If config was empty, try reload (maybe file created)
        if not self.manager.process_defs:
             try:
                self.manager.load_config(self.procfile_path)
             except FileNotFoundError:
                pass

        current_keys = set(table.rows.keys())

        # Add defined processes
        for name in self.manager.process_defs:
            status = "Stopped"
            pid = "-"
            status_color = "red"

            if name in self.manager.processes:
                proc = self.manager.processes[name]
                if proc.returncode is None:
                    status = "Running"
                    status_color = "green"
                    pid = str(proc.pid)
                else:
                    status = f"Exited ({proc.returncode})"
                    status_color = "yellow"

            status_display = f"[{status_color}]{status}[/{status_color}]"

            if name in current_keys:
                table.update_cell(name, "status", status_display)
                table.update_cell(name, "pid", pid)
            else:
                table.add_row(name, status_display, pid, key=name)

        # Update buttons based on selection
        if self.selected_process:
            self._update_buttons(self.selected_process)

    def _update_buttons(self, name: str) -> None:
        is_running = False
        if name in self.manager.processes:
            proc = self.manager.processes[name]
            if proc.returncode is None:
                is_running = True

        self.query_one("#btn-proc-start").disabled = is_running
        self.query_one("#btn-proc-stop").disabled = not is_running
        self.query_one("#btn-proc-clear").disabled = False

    def on_process_output(self, name: str, line: str) -> None:
        if name not in self.output_buffers:
            self.output_buffers[name] = deque(maxlen=1000)

        self.output_buffers[name].append(line)

        if self.selected_process == name:
            self.write_log(line)

    def write_log(self, text: str) -> None:
        log = self.query_one("#proc-log", RichLog)
        log.write(text)

    @on(DataTable.RowSelected, "#proc-table")
    def on_process_selected(self, event: DataTable.RowSelected) -> None:
        self.selected_process = event.row_key.value
        self.query_one("#proc-header").update(f"[bold]Output: {self.selected_process}[/bold]")

        # Load buffer
        log = self.query_one("#proc-log", RichLog)
        log.clear()
        if self.selected_process in self.output_buffers:
            for line in self.output_buffers[self.selected_process]:
                log.write(line)

        self._update_buttons(self.selected_process)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id

        if btn_id == "btn-proc-refresh":
            try:
                self.manager.load_config(self.procfile_path)
                self.refresh_table()
                self.notify("Procfile reloaded.")
            except FileNotFoundError:
                self.notify("Procfile not found.", severity="error")

        elif btn_id == "btn-proc-stop-all":
            self.notify("Stopping all processes...")
            await self.manager.stop_all()
            self.notify("All processes stopped.")
            self.refresh_table()

        elif btn_id == "btn-proc-start":
            if self.selected_process:
                self.notify(f"Starting {self.selected_process}...")
                try:
                    await self.manager.start_process(self.selected_process, on_output=self.on_process_output)
                    self.refresh_table()
                except Exception as e:
                    self.notify(f"Error: {e}", severity="error")

        elif btn_id == "btn-proc-stop":
            if self.selected_process:
                self.notify(f"Stopping {self.selected_process}...")
                await self.manager.stop_process(self.selected_process)
                self.refresh_table()

        elif btn_id == "btn-proc-clear":
            if self.selected_process:
                if self.selected_process in self.output_buffers:
                    self.output_buffers[self.selected_process].clear()
                self.query_one("#proc-log", RichLog).clear()
