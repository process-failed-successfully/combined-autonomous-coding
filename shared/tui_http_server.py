from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (Button, Input, Label, RichLog, TabbedContent,
                             TabPane)

from shared.http_server_lab import HttpServerManager


class HttpServerLabTab(Container):
    """Tab for HTTP Server (Static & Echo)."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = HttpServerManager()
        # Set callback
        self.manager.set_log_callback(self.log_message)

    def log_message(self, message: str) -> None:
        # Check if widget is mounted
        try:
            log = self.query_one("#http-server-log", RichLog)
            log.write(message)
        except Exception:  # nosec B110
            # Widget might not be mounted yet or app is closing
            pass

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]HTTP Server Lab[/bold]", classes="welcome-text")

            with TabbedContent(id="tabs"):
                with TabPane("Static Server", id="tab-static"):
                    with Horizontal(classes="stat-box"):
                        yield Label("Path:")
                        yield Input(value=str(self.project_dir), id="static-path")
                        yield Label("Port:")
                        yield Input(value="8000", id="static-port", type="integer")
                        yield Button("Start", id="btn-static-start", variant="primary")
                        yield Button("Stop", id="btn-static-stop", variant="error", disabled=True)

                with TabPane("Echo Server", id="tab-echo"):
                    with Horizontal(classes="stat-box"):
                        yield Label("Port:")
                        yield Input(value="8001", id="echo-port", type="integer")
                        yield Button("Start", id="btn-echo-start", variant="primary")
                        yield Button("Stop", id="btn-echo-stop", variant="error", disabled=True)

            yield Label("[bold]Server Log[/bold]")
            yield RichLog(id="http-server-log", wrap=True, highlight=True, markup=True)

    @on(Button.Pressed, "#btn-static-start")
    async def on_static_start(self) -> None:
        path = self.query_one("#static-path", Input).value
        port_str = self.query_one("#static-port", Input).value

        try:
            port = int(port_str)
        except ValueError:
            self.notify("Invalid port.", severity="error")
            return

        self.notify(f"Starting Static Server on {port}...")
        try:
            await self.manager.start_static(path, port)
            self.query_one("#btn-static-start").disabled = True
            self.query_one("#btn-static-stop").disabled = False
            # Disable other start buttons to prevent conflict if manager is singleton-ish per instance
            self.query_one("#btn-echo-start").disabled = True

            self.notify("Server started.")
        except Exception as e:
            self.notify(f"Failed to start: {e}", severity="error")

    @on(Button.Pressed, "#btn-static-stop")
    async def on_static_stop(self) -> None:
        await self.manager.stop()
        self.query_one("#btn-static-start").disabled = False
        self.query_one("#btn-static-stop").disabled = True
        self.query_one("#btn-echo-start").disabled = False
        self.notify("Server stopped.")

    @on(Button.Pressed, "#btn-echo-start")
    async def on_echo_start(self) -> None:
        port_str = self.query_one("#echo-port", Input).value

        try:
            port = int(port_str)
        except ValueError:
            self.notify("Invalid port.", severity="error")
            return

        self.notify(f"Starting Echo Server on {port}...")
        try:
            await self.manager.start_echo(port)
            self.query_one("#btn-echo-start").disabled = True
            self.query_one("#btn-echo-stop").disabled = False
            self.query_one("#btn-static-start").disabled = True

            self.notify("Server started.")
        except Exception as e:
            self.notify(f"Failed to start: {e}", severity="error")

    @on(Button.Pressed, "#btn-echo-stop")
    async def on_echo_stop(self) -> None:
        await self.manager.stop()
        self.query_one("#btn-echo-start").disabled = False
        self.query_one("#btn-echo-stop").disabled = True
        self.query_one("#btn-static-start").disabled = False
        self.notify("Server stopped.")
