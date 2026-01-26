from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Button, Label, RichLog, DataTable, Static
from textual.containers import Container, Horizontal, Vertical
from textual import on
import asyncio

from shared.docker_manager import DockerManager

class DockerTab(Container):
    """Tab for managing Docker containers."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = DockerManager()
        self.selected_container = None
        self.timer = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: Container List
            with Vertical(id="docker-list-container", classes="stat-box"):
                yield Label("[bold]Containers[/bold]")
                yield DataTable(id="docker-table")
                yield Button("Refresh", id="btn-docker-refresh", variant="default")

            # Right Pane: Logs & Actions
            with Vertical(id="docker-details-container"):
                yield Label("[bold]Container Details & Logs[/bold]", id="docker-header")
                yield RichLog(id="docker-log", wrap=True, highlight=True, markup=True)

                with Horizontal(id="docker-actions"):
                    yield Button("Start", id="btn-docker-start", variant="success", disabled=True)
                    yield Button("Stop", id="btn-docker-stop", variant="error", disabled=True)
                    yield Button("Restart", id="btn-docker-restart", variant="warning", disabled=True)
                    yield Button("Fetch Logs", id="btn-docker-logs", variant="primary", disabled=True)

    def on_mount(self) -> None:
        table = self.query_one("#docker-table", DataTable)
        table.cursor_type = "row"
        table.add_column("ID", key="id")
        table.add_column("Image", key="image")
        table.add_column("Status", key="status")
        table.add_column("Names", key="names")

        # Start polling timer (2s)
        self.timer = self.set_interval(2.0, self.refresh_ui)
        self.refresh_ui()

    def on_unmount(self) -> None:
        if self.timer:
            self.timer.stop()

    def refresh_ui(self) -> None:
        # Run in thread to avoid blocking UI
        asyncio.create_task(self._async_refresh())

    async def _async_refresh(self) -> None:
        containers = await asyncio.to_thread(self.manager.list_containers)

        # Update Table on main thread
        try:
            table = self.query_one("#docker-table", DataTable)
        except Exception:
            return # Widget might be unmounted

        current_keys = set(table.rows.keys())
        new_keys = set()

        for c in containers:
            cid = c.get("ID", "")[:12] # Short ID
            new_keys.add(cid)

            status = c.get("Status", "")
            status_color = "green" if "Up" in status else "red"
            status_display = f"[{status_color}]{status}[/{status_color}]"

            names = c.get("Names", "")
            image = c.get("Image", "")

            if cid in current_keys:
                table.update_cell(cid, "status", status_display)
            else:
                table.add_row(cid, image, status_display, names, key=cid)

        # Remove stale rows
        for key in current_keys - new_keys:
            table.remove_row(key)

        # Update buttons state based on selected container status
        if self.selected_container:
            # Find the container dict (handle short ID matching)
            container = next((c for c in containers if c.get("ID", "").startswith(self.selected_container)), None)
            self._update_buttons(container)

    def _update_buttons(self, container) -> None:
        if not container:
            self.query_one("#btn-docker-start").disabled = True
            self.query_one("#btn-docker-stop").disabled = True
            self.query_one("#btn-docker-restart").disabled = True
            self.query_one("#btn-docker-logs").disabled = True
            return

        status = container.get("Status", "")
        is_running = "Up" in status

        self.query_one("#btn-docker-logs").disabled = False

        if is_running:
            self.query_one("#btn-docker-start").disabled = True
            self.query_one("#btn-docker-stop").disabled = False
            self.query_one("#btn-docker-restart").disabled = False
        else:
            self.query_one("#btn-docker-start").disabled = False
            self.query_one("#btn-docker-stop").disabled = True
            self.query_one("#btn-docker-restart").disabled = True

    @on(DataTable.RowSelected, "#docker-table")
    def on_container_selected(self, event: DataTable.RowSelected) -> None:
        self.selected_container = event.row_key.value
        self.query_one("#docker-header").update(f"[bold]Container: {self.selected_container}[/bold]")
        self.refresh_ui() # Update buttons immediately
        self.fetch_logs()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if not self.selected_container:
            return

        cid = self.selected_container
        btn_id = event.button.id

        if btn_id == "btn-docker-refresh":
            self.refresh_ui()
            self.notify("Refreshing...")

        elif btn_id == "btn-docker-logs":
            self.fetch_logs()

        elif btn_id == "btn-docker-start":
            self.notify(f"Starting {cid}...")
            await asyncio.to_thread(self.manager.start_container, cid)
            self.refresh_ui()

        elif btn_id == "btn-docker-stop":
            self.notify(f"Stopping {cid}...")
            await asyncio.to_thread(self.manager.stop_container, cid)
            self.refresh_ui()

        elif btn_id == "btn-docker-restart":
            self.notify(f"Restarting {cid}...")
            await asyncio.to_thread(self.manager.restart_container, cid)
            self.refresh_ui()

    def fetch_logs(self) -> None:
        if not self.selected_container:
            return

        asyncio.create_task(self._async_logs())

    async def _async_logs(self) -> None:
        logs = await asyncio.to_thread(self.manager.get_logs, self.selected_container, tail=200)
        try:
            log_view = self.query_one("#docker-log", RichLog)
            log_view.clear()
            log_view.write(logs)
        except Exception:
            pass
