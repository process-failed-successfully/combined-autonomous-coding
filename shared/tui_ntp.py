import asyncio
from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Label, Button, Input, RichLog
from textual import on, work
from textual.worker import get_current_worker
from shared.ntp_lab import NtpLabManager

class NtpLabTab(Container):
    """Tab for experimenting with NTP Server queries."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = NtpLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]NTP Lab[/bold]", classes="welcome-text")

            with Vertical(classes="stat-box"):
                yield Label("NTP Server:")
                with Horizontal():
                    yield Input(placeholder="pool.ntp.org", id="ntp-server", value="pool.ntp.org")
                    yield Input(placeholder="123", id="ntp-port", value="123", type="integer")
                    yield Button("Query Server", id="btn-ntp-query", variant="primary")

                yield Label("Output:")
                yield RichLog(id="ntp-output", highlight=True, markup=True)

    @on(Button.Pressed, "#btn-ntp-query")
    def on_query_pressed(self) -> None:
        server = self.query_one("#ntp-server", Input).value
        port_str = self.query_one("#ntp-port", Input).value
        log = self.query_one("#ntp-output", RichLog)

        if not server:
            self.notify("Server address is required.", severity="error")
            return

        try:
            port = int(port_str) if port_str else 123
        except ValueError:
            self.notify("Port must be an integer.", severity="error")
            return

        log.clear()
        log.write(f"Querying [bold]{server}:{port}[/bold]...")
        self.query_one("#btn-ntp-query").disabled = True

        self.run_query(server, port)

    @work(thread=True)
    def run_query(self, server: str, port: int) -> None:
        result = self.manager.query(server, port=port)
        worker = get_current_worker()
        if not worker.is_cancelled:
            self.app.call_from_thread(self._handle_query_result, result)

    def _handle_query_result(self, result: dict) -> None:
        self.query_one("#btn-ntp-query").disabled = False
        log = self.query_one("#ntp-output", RichLog)

        if not result.get("valid"):
            log.write(f"[red]❌ Error:[/red] {result.get('error')}")
            return

        log.write(f"[green]✅ Success! Response from {result['server']} ({result['address']})[/green]")
        log.write(f"  Version:         {result['version']}")
        log.write(f"  Mode:            {result['mode']}")
        log.write(f"  Leap Indicator:  {result['leap_indicator']}")
        log.write(f"  Stratum:         {result['stratum']}")
        log.write(f"  Reference ID:    {result['reference_id']}")
        log.write(f"  Precision:       {result['precision']}")
        log.write(f"  Offset:          [yellow]{result['offset_ms']:.3f} ms[/yellow]")
        log.write(f"  Delay:           [cyan]{result['delay_ms']:.3f} ms[/cyan]")

        log.write("\n  [bold]Timestamps:[/bold]")
        log.write(f"    Reference: {self.manager.format_timestamp(result['reference_timestamp'])}")
        log.write(f"    Origin:    {self.manager.format_timestamp(result['origin_timestamp'])}")
        log.write(f"    Receive:   {self.manager.format_timestamp(result['receive_timestamp'])}")
        log.write(f"    Transmit:  {self.manager.format_timestamp(result['transmit_timestamp'])}")
