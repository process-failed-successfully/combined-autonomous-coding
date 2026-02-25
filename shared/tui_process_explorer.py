from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Label, Button, Input, DataTable, RichLog, TabbedContent, TabPane, Select
from textual import on
from rich.syntax import Syntax
import asyncio
import json

from shared.process_explorer import ProcessExplorerManager

class ProcessExplorerTab(Container):
    """Tab for exploring and managing system processes."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = ProcessExplorerManager()
        self.selected_pid = None
        self.refresh_timer = None
        self.auto_refresh = True

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]System Process Explorer[/bold]", classes="welcome-text")

            # Controls
            with Horizontal(classes="stat-box"):
                yield Label("Filter:", classes="label")
                yield Input(placeholder="Name or PID...", id="pex-filter")

                yield Label("Sort:", classes="label")
                yield Select.from_values(["cpu", "memory", "pid", "name"], id="pex-sort", value="cpu")

                yield Button("Refresh", id="btn-pex-refresh", variant="primary")
                yield Button("Pause", id="btn-pex-pause", variant="default")

            # Process List
            with Vertical(id="pex-list-container"):
                yield DataTable(id="pex-table")

            # Details & Actions
            with Horizontal(classes="stat-box", id="pex-details-box"):
                with Vertical(id="pex-actions"):
                    yield Label("[bold]Actions[/bold]")
                    yield Button("Kill (SIGTERM)", id="btn-pex-term", variant="warning", disabled=True)
                    yield Button("Force Kill (SIGKILL)", id="btn-pex-kill", variant="error", disabled=True)
                    yield Button("Suspend", id="btn-pex-suspend", variant="default", disabled=True)
                    yield Button("Resume", id="btn-pex-resume", variant="success", disabled=True)

                with Vertical(id="pex-info"):
                    yield Label("[bold]Details[/bold]")
                    with TabbedContent():
                        with TabPane("Info"):
                            yield RichLog(id="pex-log-info", wrap=True, highlight=True, markup=True)
                        with TabPane("Environment"):
                            yield RichLog(id="pex-log-env", wrap=True, highlight=True, markup=True)
                        with TabPane("Files"):
                            yield RichLog(id="pex-log-files", wrap=True, highlight=True, markup=True)
                        with TabPane("Connections"):
                            yield RichLog(id="pex-log-net", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        table = self.query_one("#pex-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("PID", "Name", "User", "Status", "CPU%", "Mem%")

        self.refresh_processes()
        self.refresh_timer = self.set_interval(2.0, self.auto_refresh_tick)

    def on_unmount(self) -> None:
        if self.refresh_timer:
            self.refresh_timer.stop()

    def auto_refresh_tick(self) -> None:
        if self.auto_refresh:
            self.refresh_processes(preserve_scroll=True)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "btn-pex-refresh":
            self.refresh_processes()
        elif btn_id == "btn-pex-pause":
            self.toggle_pause()
        elif btn_id == "btn-pex-term":
            self.kill_selected(force=False)
        elif btn_id == "btn-pex-kill":
            self.kill_selected(force=True)
        elif btn_id == "btn-pex-suspend":
            self.suspend_selected()
        elif btn_id == "btn-pex-resume":
            self.resume_selected()

    def toggle_pause(self) -> None:
        self.auto_refresh = not self.auto_refresh
        btn = self.query_one("#btn-pex-pause", Button)
        if self.auto_refresh:
            btn.label = "Pause"
            btn.variant = "default"
        else:
            btn.label = "Resume Auto-Refresh"
            btn.variant = "warning"

    def refresh_processes(self, preserve_scroll: bool = False) -> None:
        filter_text = self.query_one("#pex-filter", Input).value
        sort_by = self.query_one("#pex-sort", Select).value or "cpu"

        table = self.query_one("#pex-table", DataTable)
        current_scroll_y = table.scroll_y if preserve_scroll else 0

        # We need to clear and re-add because updating existing rows efficiently requires matching keys perfectly
        # and psutil iter might change.
        # But clearing resets selection.
        # Ideally we update existing rows if PID exists.

        procs = self.manager.list_processes(sort_by, filter_text)

        # Update table logic
        # 1. Get existing keys
        existing_keys = set(table.rows.keys())
        new_keys = set()

        for p in procs:
            pid_key = str(p['pid'])
            new_keys.add(pid_key)

            name = p.get('name', '?')
            user = p.get('username', '?')
            status = p.get('status', '?')
            cpu = f"{p.get('cpu_percent', 0.0):.1f}"
            mem = f"{p.get('memory_percent', 0.0):.1f}"

            # Color status
            if status == "running":
                status = f"[green]{status}[/green]"
            elif status == "sleeping":
                status = f"[blue]{status}[/blue]"
            elif status == "stopped":
                status = f"[red]{status}[/red]"
            elif status == "zombie":
                status = f"[bold red]{status}[/bold red]"

            if pid_key in existing_keys:
                table.update_cell(pid_key, "Name", name)
                table.update_cell(pid_key, "User", user)
                table.update_cell(pid_key, "Status", status)
                table.update_cell(pid_key, "CPU%", cpu)
                table.update_cell(pid_key, "Mem%", mem)
            else:
                table.add_row(str(p['pid']), name, user, status, cpu, mem, key=pid_key)

        # Remove stale rows
        for key in existing_keys - new_keys:
            table.remove_row(key)

        # Restore scroll if possible (Textual usually handles this if rows persist)
        # But if we clear, we lose it. Here we update, so it should be fine.

    @on(DataTable.RowSelected, "#pex-table")
    def on_process_selected(self, event: DataTable.RowSelected) -> None:
        pid_str = event.row_key.value
        self.selected_pid = int(pid_str)
        self.update_details()
        self.enable_actions(True)

    def enable_actions(self, enable: bool) -> None:
        for bid in ["btn-pex-term", "btn-pex-kill", "btn-pex-suspend", "btn-pex-resume"]:
            self.query_one(f"#{bid}", Button).disabled = not enable

    def update_details(self) -> None:
        if not self.selected_pid:
            return

        details = self.manager.get_process_details(self.selected_pid)

        # Info Tab
        log_info = self.query_one("#pex-log-info", RichLog)
        log_info.clear()
        if "error" in details:
            log_info.write(f"[bold red]Error:[/bold red] {details['error']}")
            return

        log_info.write(f"[bold]PID:[/bold] {details.get('pid')}")
        log_info.write(f"[bold]Name:[/bold] {details.get('name')}")
        log_info.write(f"[bold]User:[/bold] {details.get('username')}")
        log_info.write(f"[bold]Status:[/bold] {details.get('status')}")
        log_info.write(f"[bold]Command:[/bold] {details.get('cmdline')}")
        log_info.write(f"[bold]CWD:[/bold] {details.get('cwd')}")
        log_info.write(f"[bold]EXE:[/bold] {details.get('exe')}")
        log_info.write(f"[bold]Threads:[/bold] {details.get('num_threads')}")
        log_info.write(f"[bold]Nice:[/bold] {details.get('nice')}")

        # Env Tab
        log_env = self.query_one("#pex-log-env", RichLog)
        log_env.clear()
        env = details.get('environ', {})
        if env:
            for k, v in env.items():
                log_env.write(f"[bold blue]{k}[/bold blue]={v}")
        else:
            log_env.write("No environment variables accessible.")

        # Files Tab
        log_files = self.query_one("#pex-log-files", RichLog)
        log_files.clear()
        files = details.get('open_files', [])
        if files:
            for f in files:
                log_files.write(f)
        else:
            log_files.write("No open files accessible.")

        # Connections Tab
        log_net = self.query_one("#pex-log-net", RichLog)
        log_net.clear()
        conns = details.get('connections', [])
        if conns:
            for c in conns:
                log_net.write(c)
        else:
            log_net.write("No network connections accessible.")

    def kill_selected(self, force: bool) -> None:
        if not self.selected_pid: return
        if self.manager.kill_process(self.selected_pid, force):
            self.notify(f"Process {self.selected_pid} killed.")
            self.refresh_processes()
        else:
            self.notify("Failed to kill process.", severity="error")

    def suspend_selected(self) -> None:
        if not self.selected_pid: return
        if self.manager.suspend_process(self.selected_pid):
            self.notify(f"Process {self.selected_pid} suspended.")
            self.refresh_processes()
        else:
            self.notify("Failed to suspend process.", severity="error")

    def resume_selected(self) -> None:
        if not self.selected_pid: return
        if self.manager.resume_process(self.selected_pid):
            self.notify(f"Process {self.selected_pid} resumed.")
            self.refresh_processes()
        else:
            self.notify("Failed to resume process.", severity="error")
