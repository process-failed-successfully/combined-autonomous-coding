from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Input, Label, RichLog, Select
from textual import on
import threading
from shared.http_server_lab import HttpServerManager

class HttpServerLabTab(Container):
    """Tab for running a local HTTP server."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = HttpServerManager(project_dir)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]HTTP Server Lab[/bold]", classes="welcome-text")

            # Configuration
            with Horizontal(classes="stat-box"):
                with Vertical():
                    yield Label("Port:")
                    yield Input(placeholder="8080", value="8080", id="http-server-port")

                with Vertical():
                    yield Label("Mode:")
                    yield Select.from_values(["static", "echo"], id="http-server-mode", value="static")

                with Vertical(id="http-server-dir-container"):
                    yield Label("Directory (Static Mode):")
                    yield Input(placeholder="./", value="./", id="http-server-dir")

            # Actions
            with Horizontal(classes="stat-box"):
                yield Button("Start Server", id="btn-http-start", variant="success")
                yield Button("Stop Server", id="btn-http-stop", variant="error", disabled=True)
                yield Button("Clear Log", id="btn-http-clear", variant="default")

            # Logs
            with VerticalScroll(classes="stat-box"):
                yield Label("[bold]Access Log[/bold]")
                yield RichLog(id="http-server-log", wrap=True, highlight=True, markup=True)

    @on(Select.Changed, "#http-server-mode")
    def on_mode_changed(self, event: Select.Changed) -> None:
        mode = event.value
        dir_input = self.query_one("#http-server-dir", Input)
        if mode == "static":
            dir_input.disabled = False
        else:
            dir_input.disabled = True

    @on(Button.Pressed, "#btn-http-start")
    def on_start(self) -> None:
        port_val = self.query_one("#http-server-port", Input).value
        try:
            port = int(port_val)
        except ValueError:
            self.notify("Invalid port.", severity="error")
            return

        mode = self.query_one("#http-server-mode", Select).value
        # Handle case where value might be Select.BLANK or similar if unset
        if not mode:
             mode = "static"

        directory = self.query_one("#http-server-dir", Input).value

        self.query_one("#http-server-log", RichLog).write(f"[bold yellow]Starting {mode} server on port {port}...[/bold yellow]")

        try:
            # We pass a lambda that calls call_from_thread to update UI safely
            self.manager.start_server(
                port=port,
                directory=directory,
                mode=mode,
                callback=self.log_message
            )

            self.query_one("#btn-http-start").disabled = True
            self.query_one("#btn-http-stop").disabled = False
            self.query_one("#http-server-port").disabled = True
            self.query_one("#http-server-mode").disabled = True
            self.query_one("#http-server-dir").disabled = True

        except Exception as e:
            self.notify(f"Failed to start: {e}", severity="error")

    @on(Button.Pressed, "#btn-http-stop")
    def on_stop(self) -> None:
        self.query_one("#http-server-log", RichLog).write("[bold yellow]Stopping server...[/bold yellow]")
        try:
            threading.Thread(target=self._stop_background, daemon=True).start()
        except Exception as e:
            self.notify(f"Error stopping: {e}", severity="error")

    def _stop_background(self) -> None:
        self.manager.stop_server()
        # Update UI back on main thread
        self.app.call_from_thread(self._post_stop_ui_update)

    def _post_stop_ui_update(self) -> None:
        try:
            self.query_one("#btn-http-start").disabled = False
            self.query_one("#btn-http-stop").disabled = True
            self.query_one("#http-server-port").disabled = False
            self.query_one("#http-server-mode").disabled = False
            self.query_one("#http-server-dir").disabled = False
            self.notify("Server stopped.")
        except Exception:
            pass

    @on(Button.Pressed, "#btn-http-clear")
    def on_clear(self) -> None:
        self.query_one("#http-server-log", RichLog).clear()

    def log_message(self, message: str) -> None:
        """Callback for the manager to log messages safely."""
        # Check if widget is still mounted to avoid errors
        # Note: self.app might not be available if unmounted, but call_from_thread is on app
        try:
            if self.is_mounted:
                log_widget = self.query_one("#http-server-log", RichLog)
                self.app.call_from_thread(log_widget.write, message)
        except Exception:
            pass
