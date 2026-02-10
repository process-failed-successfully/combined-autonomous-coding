from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Button, Input, Label, RichLog, DataTable
from textual.containers import Container, Horizontal, Vertical
from textual import on

from shared.process_manager import ServiceManager
from shared.serve import ServeManager

class ServicesTab(Container):
    """Tab for managing background services."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = ServiceManager(project_dir)
        self.serve_manager = ServeManager(project_dir)
        self.selected_service = None
        self.timer = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: Services List
            with Vertical(id="services-list-container", classes="stat-box"):
                yield Label("[bold]Services[/bold]")
                yield DataTable(id="services-table")

                with Horizontal():
                    yield Input(placeholder="Custom command...", id="services-new-cmd")
                    yield Button("Add", id="btn-services-add", variant="primary")

                yield Button("Detect & Add Dev Server", id="btn-services-detect", variant="warning")

            # Right Pane: Details & Logs
            with Vertical(id="services-details-container"):
                yield Label("[bold]Service Logs[/bold]", id="services-header")
                yield RichLog(id="services-log", wrap=True, highlight=True, markup=True)

                with Horizontal(id="services-actions"):
                    yield Button("Start", id="btn-services-start", variant="success", disabled=True)
                    yield Button("Stop", id="btn-services-stop", variant="error", disabled=True)
                    yield Button("Restart", id="btn-services-restart", variant="warning", disabled=True)
                    yield Button("Clear Logs", id="btn-services-clear", variant="default", disabled=True)

    def on_mount(self) -> None:
        table = self.query_one("#services-table", DataTable)
        table.cursor_type = "row"
        table.add_column("Name", key="name")
        table.add_column("Status", key="status")
        table.add_column("PID", key="pid")

        # Start polling timer (1s)
        self.timer = self.set_interval(1.0, self.refresh_ui)

    def on_unmount(self) -> None:
        if self.timer:
            self.timer.stop()

    def refresh_ui(self) -> None:
        # Refresh Table
        try:
            table = self.query_one("#services-table", DataTable)
        except Exception:
            # Widget might be unmounting or not ready
            return

        services = self.manager.list_services()

        current_keys = set(table.rows.keys())

        for svc in services:
            status_color = "red"
            if svc.status == "Running": status_color = "green"
            elif svc.status == "Error": status_color = "yellow"

            status_display = f"[{status_color}]{svc.status}[/{status_color}]"
            pid_display = str(svc.pid) if svc.pid else "-"

            if svc.name in current_keys:
                table.update_cell(svc.name, "status", status_display)
                table.update_cell(svc.name, "pid", pid_display)
            else:
                table.add_row(svc.name, status_display, pid_display, key=svc.name)

        # Check if selected service still exists
        if self.selected_service and not self.manager.get_service(self.selected_service):
            self.selected_service = None
            self.query_one("#services-header").update("[bold]Service Logs[/bold]")
            self.query_one("#services-log", RichLog).clear()
            self._update_buttons(None)

        if self.selected_service:
            self.update_logs(self.selected_service)
            self._update_buttons(self.manager.get_service(self.selected_service))

    def _update_buttons(self, svc) -> None:
        if not svc:
            self.query_one("#btn-services-start").disabled = True
            self.query_one("#btn-services-stop").disabled = True
            self.query_one("#btn-services-restart").disabled = True
            self.query_one("#btn-services-clear").disabled = True
            return

        self.query_one("#btn-services-clear").disabled = False
        if svc.status == "Running":
            self.query_one("#btn-services-start").disabled = True
            self.query_one("#btn-services-stop").disabled = False
            self.query_one("#btn-services-restart").disabled = False
        else:
            self.query_one("#btn-services-start").disabled = False
            self.query_one("#btn-services-stop").disabled = True
            self.query_one("#btn-services-restart").disabled = True

    def update_logs(self, service_name: str) -> None:
        log_view = self.query_one("#services-log", RichLog)
        svc = self.manager.get_service(service_name)
        if not svc:
            return

        # For simplicity, we clear and rewrite.
        log_view.clear()
        for line in svc.output_buffer:
            log_view.write(line)

    @on(DataTable.RowSelected, "#services-table")
    def on_service_selected(self, event: DataTable.RowSelected) -> None:
        self.selected_service = event.row_key.value
        self.query_one("#services-header").update(f"[bold]Logs: {self.selected_service}[/bold]")
        self.refresh_ui()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id

        if btn_id == "btn-services-add":
            cmd = self.query_one("#services-new-cmd", Input).value
            if cmd:
                name = cmd.split()[0]
                base_name = name
                cnt = 1
                while self.manager.get_service(name):
                    name = f"{base_name}_{cnt}"
                    cnt += 1

                self.manager.add_service(name, cmd)
                self.query_one("#services-new-cmd", Input).value = ""
                self.refresh_ui()

        elif btn_id == "btn-services-detect":
            cmd_list, port = self.serve_manager.detect_config()
            if cmd_list:
                cmd_str = " ".join(cmd_list)
                try:
                    self.manager.add_service("DevServer", cmd_str)
                    self.notify(f"Added DevServer: {cmd_str}")
                    self.refresh_ui()
                except ValueError:
                    self.notify("DevServer already exists.", severity="warning")
            else:
                self.notify("Could not detect server config.", severity="error")

        elif btn_id == "btn-services-start":
            if self.selected_service:
                await self.manager.start_service(self.selected_service)
                self.notify(f"Started {self.selected_service}")
                self.refresh_ui()

        elif btn_id == "btn-services-stop":
            if self.selected_service:
                await self.manager.stop_service(self.selected_service)
                self.notify(f"Stopped {self.selected_service}")
                self.refresh_ui()

        elif btn_id == "btn-services-restart":
            if self.selected_service:
                await self.manager.restart_service(self.selected_service)
                self.notify(f"Restarted {self.selected_service}")
                self.refresh_ui()

        elif btn_id == "btn-services-clear":
            if self.selected_service:
                svc = self.manager.get_service(self.selected_service)
                if svc:
                    svc.output_buffer.clear()
                    self.update_logs(self.selected_service)
