import asyncio
from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Label, Button, Input, RichLog, Switch, Checkbox
from textual.containers import Container, Horizontal, Vertical, Grid
from textual import on
from shared.static_lab import StaticLabManager

class StaticLabTab(Container):
    """Tab for Static Server Lab."""

    def __init__(self, project_dir=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = None
        self.server_running = False

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Static Server Lab[/bold]", classes="welcome-text")

            with Horizontal(classes="stat-box"):
                with Vertical():
                    yield Label("Directory Path:", classes="label")
                    yield Input(placeholder=".", value=str(self.project_dir) if self.project_dir else ".", id="static-dir")

                with Vertical():
                    yield Label("Host:", classes="label")
                    yield Input(placeholder="0.0.0.0", value="0.0.0.0", id="static-host")  # nosec B104

                with Vertical():
                    yield Label("Port:", classes="label")
                    yield Input(placeholder="8000", value="8000", id="static-port")

            with Horizontal(classes="stat-box"):
                with Vertical():
                    yield Label("Upload Dir (optional):", classes="label")
                    yield Input(placeholder="", value="", id="static-upload")

                with Vertical():
                    yield Label("Auth (user:pass):", classes="label")
                    yield Input(placeholder="", value="", id="static-auth")

            with Horizontal(classes="stat-box"):
                with Vertical():
                    yield Label("Delay (s):", classes="label")
                    yield Input(placeholder="0.0", value="0.0", id="static-delay")
                with Vertical():
                    yield Label("Error Rate (0.0-1.0):", classes="label")
                    yield Input(placeholder="0.0", value="0.0", id="static-error")

            with Horizontal(classes="stat-box"):
                yield Checkbox("CORS", id="cb-cors", value=False)
                yield Checkbox("SSL", id="cb-ssl", value=False)
                yield Checkbox("SPA Mode", id="cb-spa", value=False)

            with Horizontal(classes="stat-box"):
                yield Button("Start Server", id="btn-static-start", variant="primary")
                yield Button("Stop Server", id="btn-static-stop", variant="error", disabled=True)

            yield Label("[bold]Server Log[/bold]")
            yield RichLog(id="static-log", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        pass

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-static-start":
            await self.start_server()
        elif event.button.id == "btn-static-stop":
            await self.stop_server()

    async def start_server(self) -> None:
        directory = self.query_one("#static-dir", Input).value
        host = self.query_one("#static-host", Input).value
        port_str = self.query_one("#static-port", Input).value
        upload = self.query_one("#static-upload", Input).value
        auth = self.query_one("#static-auth", Input).value
        delay_str = self.query_one("#static-delay", Input).value
        error_str = self.query_one("#static-error", Input).value

        cors = self.query_one("#cb-cors", Checkbox).value
        ssl = self.query_one("#cb-ssl", Checkbox).value
        spa = self.query_one("#cb-spa", Checkbox).value

        if not port_str.isdigit():
            self.notify("Invalid port.", severity="error")
            return

        try:
            delay = float(delay_str)
            error_rate = float(error_str)
        except ValueError:
            self.notify("Invalid delay or error rate. Must be numeric.", severity="error")
            return

        port = int(port_str)

        config = {
            "port": port,
            "host": host,
            "directory": directory,
            "cors": cors,
            "delay": delay,
            "error_rate": error_rate,
            "auth": auth if auth else None,
            "upload_dir": upload if upload else None,
            "spa": spa,
            "ssl": ssl,
            "on_log": self.log_message
        }

        self.manager = StaticLabManager(config)

        self.query_one("#static-log", RichLog).write(f"[bold green]Starting Static Server on {host}:{port}...[/bold green]")

        self.update_ui_running()
        # Run in thread
        asyncio.create_task(self._run_server())

    async def _run_server(self) -> None:
        try:
            await asyncio.to_thread(self.manager.run)
        except OSError as e:
            self.notify(f"Error starting server: {e}", severity="error")
            self.log_message(f"[bold red]Error: {e}[/bold red]", "error")
            self.call_later(self.reset_ui)
        except Exception as e:
            self.notify(f"Unexpected error: {e}", severity="error")
            self.log_message(f"[bold red]Error: {e}[/bold red]", "error")
            self.call_later(self.reset_ui)

    def log_message(self, message: str, level: str = "info", **kwargs) -> None:
        """Callback for logging from the server."""
        self.app.call_from_thread(self._write_log, message, level)

    def _write_log(self, message: str, level: str) -> None:
        try:
            log_view = self.query_one("#static-log", RichLog)
        except Exception:
            return

        formatted_msg = message
        if level == "error":
            formatted_msg = f"[bold red]{message}[/bold red]"
        elif level == "info":
            for method in ["GET", "POST", "PUT", "DELETE", "CONNECT", "HEAD", "OPTIONS", "PATCH"]:
                if message.startswith(method):
                    formatted_msg = message.replace(method, f"[bold cyan]{method}[/bold cyan]", 1)
                    break

        log_view.write(formatted_msg)

    def update_ui_running(self) -> None:
        self.server_running = True
        self.query_one("#btn-static-start").disabled = True
        self.query_one("#btn-static-stop").disabled = False

        # Disable inputs
        for input_id in ["#static-dir", "#static-host", "#static-port", "#static-upload", "#static-auth", "#static-delay", "#static-error"]:
            self.query_one(input_id).disabled = True

        for cb_id in ["#cb-cors", "#cb-ssl", "#cb-spa"]:
            self.query_one(cb_id).disabled = True

        self.notify("Server started.")

    async def stop_server(self) -> None:
        if self.manager:
            self.notify("Stopping server...")
            # Run stop in a thread to prevent blocking the UI
            await asyncio.to_thread(self.manager.stop)
            self.server_running = False
            self.reset_ui()
            self.query_one("#static-log", RichLog).write("[bold yellow]Server stopped.[/bold yellow]")

    def reset_ui(self) -> None:
        self.query_one("#btn-static-start").disabled = False
        self.query_one("#btn-static-stop").disabled = True

        # Enable inputs
        for input_id in ["#static-dir", "#static-host", "#static-port", "#static-upload", "#static-auth", "#static-delay", "#static-error"]:
            self.query_one(input_id).disabled = False

        for cb_id in ["#cb-cors", "#cb-ssl", "#cb-spa"]:
            self.query_one(cb_id).disabled = False
