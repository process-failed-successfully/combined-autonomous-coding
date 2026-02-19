import asyncio
from textual.app import ComposeResult
from textual.widgets import Label, Button, Input, RichLog
from textual.containers import Container, Horizontal, Vertical
from shared.proxy_lab import ProxyLabManager


class ProxyLabTab(Container):
    """Tab for Proxy Lab."""

    def __init__(self, project_dir=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = ProxyLabManager()  # Default 8080
        self.proxy_running = False

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Proxy Lab[/bold]", classes="welcome-text")

            with Horizontal(classes="stat-box"):
                yield Label("Host:", classes="label")
                yield Input(placeholder="127.0.0.1", value="127.0.0.1", id="proxy-host")
                yield Label("Port:", classes="label")
                yield Input(placeholder="8080", value="8080", id="proxy-port")
                yield Button("Start Proxy", id="btn-proxy-start", variant="primary")
                yield Button("Stop Proxy", id="btn-proxy-stop", variant="error", disabled=True)

            yield Label("[bold]Request Log[/bold]")
            yield RichLog(id="proxy-log", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        pass

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-proxy-start":
            await self.start_proxy()
        elif event.button.id == "btn-proxy-stop":
            await self.stop_proxy()

    async def start_proxy(self) -> None:
        host = self.query_one("#proxy-host", Input).value
        port_str = self.query_one("#proxy-port", Input).value

        if not port_str.isdigit():
            self.notify("Invalid port.", severity="error")
            return

        port = int(port_str)
        self.manager = ProxyLabManager(port=port, host=host)

        self.query_one("#proxy-log", RichLog).write(f"[bold green]Starting proxy on {host}:{port}...[/bold green]")

        self.update_ui_running()
        # Run in thread
        asyncio.create_task(self._run_server())

    async def _run_server(self) -> None:
        try:
            await asyncio.to_thread(self.manager.start, on_log=self.log_message)
        except OSError as e:
            self.notify(f"Error starting proxy: {e}", severity="error")
            self.log_message(f"[bold red]Error: {e}[/bold red]", "error")
            self.call_later(self.reset_ui)
        except Exception as e:
            self.notify(f"Unexpected error: {e}", severity="error")
            self.log_message(f"[bold red]Error: {e}[/bold red]", "error")
            self.call_later(self.reset_ui)

    def log_message(self, message: str, level: str = "info", **kwargs) -> None:
        """Callback for logging from the proxy server."""
        # This is called from the server thread, so use call_from_thread

        # Use simple deferred lookup since query_one might be unsafe from thread?
        # call_from_thread handles the context switch.
        self.app.call_from_thread(self._write_log, message, level)

    def _write_log(self, message: str, level: str) -> None:
        log_view = self.query_one("#proxy-log", RichLog)

        formatted_msg = message
        if level == "response":
            # message format: "  -> 200 (0.001s, size: 123)"
            try:
                parts = message.strip().split()
                # parts[0] is "->"
                status_code = int(parts[1])
                color = "green" if 200 <= status_code < 300 else "yellow" if 300 <= status_code < 400 else "red"
                formatted_msg = message.replace(str(status_code), f"[{color}]{status_code}[/{color}]", 1)
            except Exception:
                pass
        elif level == "error":
            formatted_msg = f"[bold red]{message}[/bold red]"
        elif level == "info":
            # Highlight method
            for method in ["GET", "POST", "PUT", "DELETE", "CONNECT", "HEAD", "OPTIONS", "PATCH"]:
                if message.startswith(method):
                    formatted_msg = message.replace(method, f"[bold cyan]{method}[/bold cyan]", 1)
                    break

        log_view.write(formatted_msg)

    def update_ui_running(self) -> None:
        self.proxy_running = True
        self.query_one("#btn-proxy-start").disabled = True
        self.query_one("#btn-proxy-stop").disabled = False
        self.query_one("#proxy-host").disabled = True
        self.query_one("#proxy-port").disabled = True
        self.notify("Proxy started.")

    async def stop_proxy(self) -> None:
        self.notify("Stopping proxy...")
        self.manager.stop()
        self.proxy_running = False
        self.reset_ui()
        self.query_one("#proxy-log", RichLog).write("[bold yellow]Proxy stopped.[/bold yellow]")

    def reset_ui(self) -> None:
        self.query_one("#btn-proxy-start").disabled = False
        self.query_one("#btn-proxy-stop").disabled = True
        self.query_one("#proxy-host").disabled = False
        self.query_one("#proxy-port").disabled = False
