from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Button, Label, RichLog, DataTable, TabbedContent, TabPane, Input
from textual.containers import Container, Horizontal, Vertical
from textual import on
import asyncio

from shared.sys_lab import SysLabManager


class SysTab(Container):
    """Tab for managing system resources."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = SysLabManager(project_dir)
        self.selected_process = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: Main Content
            with Vertical(id="sys-main-container", classes="stat-box"):
                with TabbedContent(id="sys-tabs"):
                    with TabPane("System Info", id="tab-sys-info"):
                        yield RichLog(id="sys-info-log", wrap=True, highlight=True, markup=True)

                    with TabPane("Processes", id="tab-sys-proc"):
                        with Horizontal(classes="controls-bar"):
                            yield Label("Sort:")
                            yield Button("CPU", id="btn-sort-cpu", variant="primary")
                            yield Button("Mem", id="btn-sort-mem", variant="default")
                            yield Button("PID", id="btn-sort-pid", variant="default")
                            yield Label("Filter:")
                            yield Input(placeholder="Process name...", id="proc-filter", classes="flex-1")
                            yield Button("Refresh", id="btn-proc-refresh", variant="success")
                        yield DataTable(id="sys-proc-table")

            # Right Pane: Actions
            with Vertical(id="sys-actions-container"):
                yield Label("[bold]Actions[/bold]", id="sys-actions-header")
                yield Button("Kill Process", id="btn-sys-kill", variant="error", disabled=True)
                yield RichLog(id="sys-action-log", wrap=True)

    def on_mount(self) -> None:
        # Setup Process Table
        proc_table = self.query_one("#sys-proc-table", DataTable)
        proc_table.cursor_type = "row"
        proc_table.add_column("PID", key="pid")
        proc_table.add_column("User", key="user")
        proc_table.add_column("CPU%", key="cpu")
        proc_table.add_column("Mem%", key="mem")
        proc_table.add_column("Name", key="name")
        proc_table.add_column("Command", key="cmd")

        # Initial Load
        self.refresh_sys_info()
        self.refresh_processes("cpu")

    def refresh_sys_info(self) -> None:
        info = self.manager.get_system_info()
        log_view = self.query_one("#sys-info-log", RichLog)
        log_view.clear()

        log_view.write("[bold cyan]--- System Information ---[/bold cyan]")
        log_view.write(f"[bold]OS:[/bold] {info['system']['os']}")
        log_view.write(f"[bold]Kernel:[/bold] {info['system']['version']}")
        log_view.write(f"[bold]Processor:[/bold] {info['system']['processor']}")

        log_view.write("\n[bold cyan]--- CPU ---[/bold cyan]")
        log_view.write(f"[bold]Physical Cores:[/bold] {info['cpu']['physical_cores']}")
        log_view.write(f"[bold]Logical Cores:[/bold] {info['cpu']['logical_cores']}")
        log_view.write(f"[bold]Usage:[/bold] {info['cpu']['usage_percent']}%")

        log_view.write("\n[bold cyan]--- Memory ---[/bold cyan]")
        total_mem = self.manager.format_bytes(info['memory']['total'])
        used_mem = self.manager.format_bytes(info['memory']['used'])
        log_view.write(f"[bold]Usage:[/bold] {used_mem} / {total_mem} ({info['memory']['percent']}%)")

        log_view.write("\n[bold cyan]--- Disk (/) ---[/bold cyan]")
        total_disk = self.manager.format_bytes(info['disk']['root_total'])
        used_disk = self.manager.format_bytes(info['disk']['root_used'])
        log_view.write(f"[bold]Usage:[/bold] {used_disk} / {total_disk} ({info['disk']['root_percent']}%)")

    def refresh_processes(self, sort_by: str = "cpu") -> None:
        filter_text = self.query_one("#proc-filter", Input).value
        procs = self.manager.list_processes(sort_by=sort_by, limit=50, filter_name=filter_text)

        table = self.query_one("#sys-proc-table", DataTable)
        table.clear()

        for p in procs:
            pid = str(p['pid'])
            user = p['username'] or "?"
            cpu = f"{p['cpu_percent']:.1f}" if p['cpu_percent'] is not None else "?"
            mem = f"{p['memory_percent']:.1f}" if p['memory_percent'] is not None else "?"
            name = p['name'] or "?"
            cmd = p['cmdline'] or ""

            table.add_row(pid, user, cpu, mem, name, cmd, key=f"proc:{pid}")

        self.selected_process = None
        self.query_one("#btn-sys-kill").disabled = True

    @on(DataTable.RowSelected)
    def on_row_selected(self, event: DataTable.RowSelected) -> None:
        if not event.row_key.value:
            return

        if event.row_key.value.startswith("proc:"):
            pid = int(event.row_key.value.split(":")[1])
            self.selected_process = pid
            self.query_one("#btn-sys-kill").disabled = False
            self.query_one("#sys-actions-header", Label).update(f"[bold]Actions for PID: {pid}[/bold]")

    @on(Input.Submitted, "#proc-filter")
    def on_filter_submitted(self) -> None:
        self.refresh_processes()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-sort-cpu":
            self.refresh_processes("cpu")
        elif event.button.id == "btn-sort-mem":
            self.refresh_processes("mem")
        elif event.button.id == "btn-sort-pid":
            self.refresh_processes("pid")
        elif event.button.id == "btn-proc-refresh":
            self.refresh_processes()
            self.refresh_sys_info()
            self.notify("System info and processes refreshed.")
        elif event.button.id == "btn-sys-kill":
            if self.selected_process:
                result = await asyncio.to_thread(self.manager.kill_process, pid=self.selected_process)
                log = self.query_one("#sys-action-log", RichLog)

                if result.get("success"):
                    log.write(f"[green]Success:[/green] {result.get('message')}")
                    self.notify("Process killed.")
                    self.refresh_processes()
                else:
                    log.write(f"[red]Error:[/red] {result.get('message')}")
                    self.notify("Failed to kill process.", severity="error")
