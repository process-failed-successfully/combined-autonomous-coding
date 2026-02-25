from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Label, Button, DataTable, Input, RichLog, TabbedContent, TabPane
from textual import on
from shared.systemd_lab import SystemdManager


class SystemdLabTab(Container):
    """Tab for managing Systemd Services."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = SystemdManager(project_dir)
        self.selected_unit = None

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Systemd Service Manager[/bold]", classes="welcome-text")

            with TabbedContent():
                # --- Tab 1: Manage Services ---
                with TabPane("Manage Services"):
                    # Service List
                    with Container(classes="stat-box"):
                        yield Label("[bold]Active Units[/bold]")
                        with Horizontal():
                            yield Input(placeholder="Filter...", id="systemd-filter")
                            yield Button("Refresh", id="btn-systemd-refresh", variant="primary")
                        yield DataTable(id="systemd-table")

                    # Controls & Details
                    with Horizontal():
                        # Controls
                        with Vertical(classes="stat-box", id="systemd-controls"):
                            yield Label("Selected Service: [bold]None[/bold]", id="lbl-systemd-selected")
                            with Horizontal():
                                yield Button("Start", id="btn-systemd-start", variant="success", disabled=True)
                                yield Button("Stop", id="btn-systemd-stop", variant="error", disabled=True)
                                yield Button("Restart", id="btn-systemd-restart", variant="warning", disabled=True)
                            with Horizontal():
                                yield Button("Enable", id="btn-systemd-enable", variant="default", disabled=True)
                                yield Button("Disable", id="btn-systemd-disable", variant="default", disabled=True)
                            yield Button("Get Logs", id="btn-systemd-logs", variant="primary", disabled=True)

                        # Output/Logs
                        with VerticalScroll(classes="stat-box", id="systemd-log-container"):
                            yield Label("[bold]Status / Logs[/bold]")
                            yield RichLog(id="systemd-log", wrap=True, highlight=True, markup=True)

                # --- Tab 2: Generate Unit ---
                with TabPane("Generate Unit"):
                    with VerticalScroll(classes="stat-box"):
                        yield Label("[bold]Create New Service[/bold]")

                        yield Label("Service Name (e.g. myapp):")
                        yield Input(placeholder="myapp", id="gen-sys-name")

                        yield Label("Command:")
                        yield Input(placeholder="/usr/bin/python3 /path/to/app.py", id="gen-sys-cmd")

                        yield Label("Description:")
                        yield Input(placeholder="My Awesome App", id="gen-sys-desc")

                        with Horizontal():
                            with Vertical():
                                yield Label("User:")
                                yield Input(placeholder="root", id="gen-sys-user", value="root")
                            with Vertical():
                                yield Label("Working Dir:")
                                yield Input(placeholder="/path/to/app", id="gen-sys-workdir")

                        yield Label("Environment (key=value,key=value):")
                        yield Input(placeholder="PORT=8080,DEBUG=1", id="gen-sys-env")

                        yield Button("Generate Unit File", id="btn-systemd-generate", variant="success")

                        yield Label("[bold]Preview / Output[/bold]")
                        yield RichLog(id="gen-sys-output", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        table = self.query_one("#systemd-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Unit", "Active", "Sub", "Description")
        self.load_units()

    def load_units(self) -> None:
        table = self.query_one("#systemd-table", DataTable)
        table.clear()

        filter_text = self.query_one("#systemd-filter", Input).value.lower()

        try:
            # We fetch all units then filter in UI to avoid spamming subprocess if typing
            units = self.manager.list_units()

            if not units:
                self.notify("No services found or systemctl failed.")
                return

            for u in units:
                if filter_text and filter_text not in u['unit'].lower():
                    continue

                # Color code status
                active_display = u['active']
                if u['active'] == "active":
                    active_display = f"[green]{u['active']}[/green]"
                elif u['active'] == "failed":
                    active_display = f"[red]{u['active']}[/red]"

                table.add_row(u['unit'], active_display, u['sub'], u['description'], key=u['unit'])

        except Exception as e:
            self.notify(f"Error listing units: {e}", severity="error")
            self.query_one("#systemd-log", RichLog).write(f"[red]Error:[/red] {e}")

    @on(Button.Pressed, "#btn-systemd-refresh")
    def on_refresh(self) -> None:
        self.load_units()
        self.notify("Refreshed.")

    @on(Input.Changed, "#systemd-filter")
    def on_filter(self) -> None:
        self.load_units()

    @on(DataTable.RowSelected, "#systemd-table")
    def on_row_selected(self, event: DataTable.RowSelected) -> None:
        unit_name = event.row_key.value
        self.selected_unit = unit_name

        self.query_one("#lbl-systemd-selected", Label).update(f"Selected Service: [bold]{unit_name}[/bold]")

        # Enable buttons
        for btn_id in ["#btn-systemd-start", "#btn-systemd-stop", "#btn-systemd-restart",
                       "#btn-systemd-enable", "#btn-systemd-disable", "#btn-systemd-logs"]:
            self.query_one(btn_id).disabled = False

        # Auto-load status
        self.show_status(unit_name)

    def show_status(self, unit_name: str) -> None:
        log = self.query_one("#systemd-log", RichLog)
        log.clear()
        log.write(f"[bold]Status for {unit_name}:[/bold]")
        try:
            status = self.manager.get_status(unit_name)
            log.write(status)
        except Exception as e:
            log.write(f"[red]Error fetching status: {e}[/red]")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-systemd-refresh":
            pass  # Handled by @on
        elif event.button.id in ["btn-systemd-start", "btn-systemd-stop", "btn-systemd-restart",
                                 "btn-systemd-enable", "btn-systemd-disable"]:
            action = event.button.id.replace("btn-systemd-", "")
            await self.control_service(action)
        elif event.button.id == "btn-systemd-logs":
            self.get_logs()
        elif event.button.id == "btn-systemd-generate":
            self.generate_unit()

    async def control_service(self, action: str) -> None:
        if not self.selected_unit:
            return

        self.notify(f"{action.capitalize()}ing {self.selected_unit}...")
        log = self.query_one("#systemd-log", RichLog)
        log.write(f"\n[bold yellow]Executing: {action} {self.selected_unit}...[/bold yellow]")

        import asyncio
        try:
            success, msg = await asyncio.to_thread(self.manager.control_service, self.selected_unit, action)
            if success:
                log.write(f"[green]{msg}[/green]")
                self.notify(f"Service {action}ed.")
                # Refresh status and list
                self.show_status(self.selected_unit)
                self.load_units()
            else:
                log.write(f"[red]{msg}[/red]")
                self.notify(f"Failed to {action} service.", severity="error")
        except Exception as e:
            log.write(f"[red]Exception: {e}[/red]")
            self.notify(f"Error: {e}", severity="error")

    def get_logs(self) -> None:
        if not self.selected_unit:
            return

        log = self.query_one("#systemd-log", RichLog)
        log.clear()
        log.write(f"[bold]Logs for {self.selected_unit}:[/bold]")

        try:
            logs = self.manager.get_logs(self.selected_unit, lines=100)
            log.write(logs)
        except Exception as e:
            log.write(f"[red]Error fetching logs: {e}[/red]")

    def generate_unit(self) -> None:
        name = self.query_one("#gen-sys-name", Input).value
        cmd = self.query_one("#gen-sys-cmd", Input).value
        if not name or not cmd:
            self.notify("Name and Command are required.", severity="error")
            return

        desc = self.query_one("#gen-sys-desc", Input).value
        user = self.query_one("#gen-sys-user", Input).value
        workdir = self.query_one("#gen-sys-workdir", Input).value
        env_str = self.query_one("#gen-sys-env", Input).value

        env_dict = {}
        if env_str:
            for pair in env_str.split(","):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    env_dict[k.strip()] = v.strip()

        content = self.manager.generate_unit_file(
            name=name,
            command=cmd,
            user=user,
            working_dir=workdir if workdir else None,
            description=desc,
            environment=env_dict
        )

        log = self.query_one("#gen-sys-output", RichLog)
        log.clear()
        log.write("[bold green]Generated Unit Content:[/bold green]")
        log.write(content)

        # Save option?
        # For now just display. Could add a "Save to File" button next.

        self.notify("Unit generated. Copy content or save manually.")
