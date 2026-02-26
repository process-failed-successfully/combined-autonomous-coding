from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Button, Label, DataTable, Input, RichLog, Static
from textual.containers import Container, Horizontal, Vertical
from textual import on
from shared.process_explorer import ProcessExplorerManager

class ProcessExplorerTab(Container):
    """Tab for exploring and managing system processes."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = ProcessExplorerManager()
        self.selected_pid = None
        self.timer = None
        self.filter_text = ""

    def compose(self) -> ComposeResult:
        with Vertical():
            # Header / Filter
            with Horizontal(classes="stat-box"):
                yield Label("[bold]System Process Explorer[/bold]", classes="welcome-text")
                yield Input(placeholder="Filter by name or PID...", id="pex-filter")
                yield Button("Refresh", id="btn-pex-refresh", variant="default")

            # Main Table
            yield DataTable(id="pex-table")

            # Actions & Details
            with Horizontal(classes="stat-box"):
                yield Button("Details", id="btn-pex-details", variant="primary", disabled=True)
                yield Button("Suspend", id="btn-pex-suspend", variant="warning", disabled=True)
                yield Button("Resume", id="btn-pex-resume", variant="success", disabled=True)
                yield Button("Kill", id="btn-pex-kill", variant="error", disabled=True)
                yield Label("", id="pex-status-lbl")

            # Details Pane (Initially hidden or just a log area)
            yield RichLog(id="pex-details-log", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        table = self.query_one("#pex-table", DataTable)
        table.cursor_type = "row"
        # Columns: PID, Name, User, Status, CPU%, MEM%
        table.add_column("PID", key="PID")
        table.add_column("Name", key="Name")
        table.add_column("User", key="User")
        table.add_column("Status", key="Status")
        table.add_column("CPU%", key="CPU%")
        table.add_column("MEM%", key="MEM%")

        self.refresh_processes()
        # Auto-refresh every 3 seconds
        self.timer = self.set_interval(3.0, self.refresh_processes)

    def on_unmount(self) -> None:
        if self.timer:
            self.timer.stop()

    async def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "pex-filter":
            self.filter_text = event.value
            self.refresh_processes()

    def refresh_processes(self) -> None:
        table = self.query_one("#pex-table", DataTable)
        current_rows = {str(k.value): k for k in table.rows.keys()} # PID -> RowKey

        processes = self.manager.list_processes(self.filter_text)

        # Sort by CPU desc
        processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)

        # Limit to top 50 to avoid TUI lag if many processes
        processes = processes[:50]

        seen_pids = set()

        for p in processes:
            pid = str(p['pid'])
            seen_pids.add(pid)

            name = p['name']
            user = p['username'] or "?"
            status = p['status']
            cpu = f"{p['cpu_percent']:.1f}"
            mem = f"{p['memory_percent']:.1f}"

            # Color code status
            if status == "running":
                status_display = f"[green]{status}[/green]"
            elif status in ["stopped", "tracing_stop"]:
                status_display = f"[red]{status}[/red]"
            elif status == "sleeping":
                status_display = f"[dim]{status}[/dim]"
            else:
                status_display = status

            if pid in current_rows:
                # Update existing row
                table.update_cell(pid, "Name", name)
                table.update_cell(pid, "User", user)
                table.update_cell(pid, "Status", status_display)
                table.update_cell(pid, "CPU%", cpu)
                table.update_cell(pid, "MEM%", mem)
            else:
                # Add new row
                table.add_row(pid, name, user, status_display, cpu, mem, key=pid)

        # Remove stale rows
        for pid in list(current_rows.keys()):
            if pid not in seen_pids:
                table.remove_row(pid)

    @on(DataTable.RowSelected, "#pex-table")
    def on_process_selected(self, event: DataTable.RowSelected) -> None:
        self.selected_pid = int(event.row_key.value)

        # Enable buttons
        self.query_one("#btn-pex-details").disabled = False
        self.query_one("#btn-pex-suspend").disabled = False
        self.query_one("#btn-pex-resume").disabled = False
        self.query_one("#btn-pex-kill").disabled = False

        self.show_details()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-pex-refresh":
            self.refresh_processes()
        elif event.button.id == "btn-pex-details":
            self.show_details()
        elif event.button.id == "btn-pex-kill":
            self.kill_process()
        elif event.button.id == "btn-pex-suspend":
            self.suspend_process()
        elif event.button.id == "btn-pex-resume":
            self.resume_process()

    def show_details(self) -> None:
        if not self.selected_pid:
            return

        log = self.query_one("#pex-details-log", RichLog)
        log.clear()

        details = self.manager.get_process_details(self.selected_pid)

        if "error" in details:
            log.write(f"[bold red]{details['error']}[/bold red]")
            return

        log.write(f"[bold green]Process {details['pid']}: {details['name']}[/bold green]")
        log.write(f"[bold]Command:[/bold] {' '.join(details['cmdline'])}")
        log.write(f"[bold]Status:[/bold] {details['status']}")
        log.write(f"[bold]User:[/bold] {details['username']}")
        log.write(f"[bold]Threads:[/bold] {details['threads']}")
        log.write(f"[bold]Memory:[/bold] RSS={details['memory_info'].get('rss', 0)/1024/1024:.1f}MB")
        log.write(f"[bold]Environment:[/bold]")
        for k, v in details['environ'].items():
            if "KEY" in k or "TOKEN" in k or "SECRET" in k or "PASSWORD" in k:
                v = "***"
            log.write(f"  {k}={v}")

    def kill_process(self) -> None:
        if not self.selected_pid: return
        if self.manager.kill_process(self.selected_pid):
            self.notify(f"Killed process {self.selected_pid}")
            self.refresh_processes()
        else:
            self.notify(f"Failed to kill process {self.selected_pid}", severity="error")

    def suspend_process(self) -> None:
        if not self.selected_pid: return
        if self.manager.suspend_process(self.selected_pid):
            self.notify(f"Suspended process {self.selected_pid}")
            self.refresh_processes()
        else:
            self.notify(f"Failed to suspend process {self.selected_pid}", severity="error")

    def resume_process(self) -> None:
        if not self.selected_pid: return
        if self.manager.resume_process(self.selected_pid):
            self.notify(f"Resumed process {self.selected_pid}")
            self.refresh_processes()
        else:
            self.notify(f"Failed to resume process {self.selected_pid}", severity="error")
