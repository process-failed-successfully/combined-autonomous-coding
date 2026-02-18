import asyncio
import json
from pathlib import Path
from typing import Dict, Any

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Input, Label, RichLog, Select, TabbedContent, TabPane, DataTable
from textual import on

from shared.net_lab import NetLabManager

class NetDiagTab(Container):
    """Tab for Network Diagnostics (Ping, Scan, DNS, HTTP, IP)."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = NetLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Network Diagnostics[/bold]", classes="welcome-text")

            with TabbedContent():
                with TabPane("Ping"):
                    with Vertical(classes="stat-box"):
                        with Horizontal():
                            yield Label("Host:", classes="label")
                            yield Input(placeholder="e.g. google.com", id="ping-host")
                            yield Label("Count:", classes="label")
                            yield Input(placeholder="4", id="ping-count", type="integer", value="4")
                            yield Button("Ping", id="btn-ping", variant="primary")
                        yield RichLog(id="ping-log", wrap=True, highlight=True, markup=True)

                with TabPane("Port Scan"):
                    with Vertical(classes="stat-box"):
                        with Horizontal():
                            yield Label("Host:", classes="label")
                            yield Input(placeholder="e.g. localhost", id="scan-host")
                            yield Label("Ports:", classes="label")
                            yield Input(placeholder="80,443,8000-8010", id="scan-ports")
                            yield Button("Scan", id="btn-scan", variant="warning")
                        yield DataTable(id="scan-table")

                with TabPane("DNS Lookup"):
                    with Vertical(classes="stat-box"):
                        with Horizontal():
                            yield Label("Domain:", classes="label")
                            yield Input(placeholder="e.g. example.com", id="dns-domain")
                            yield Select.from_values(["A", "AAAA"], id="dns-type", value="A")
                            yield Button("Lookup", id="btn-dns", variant="success")
                        yield RichLog(id="dns-log", wrap=True, highlight=True, markup=True)

                with TabPane("HTTP Headers"):
                    with Vertical(classes="stat-box"):
                        with Horizontal():
                            yield Label("URL:", classes="label")
                            yield Input(placeholder="e.g. https://example.com", id="http-url")
                            yield Button("Fetch Headers", id="btn-http", variant="primary")
                        yield RichLog(id="http-log", wrap=True, highlight=True, markup=True)

                with TabPane("IP Info"):
                    with Vertical(classes="stat-box"):
                        yield Button("Get IP Info", id="btn-ip", variant="default")
                        yield Label("Local IP: ?", id="lbl-local-ip")
                        yield Label("Public IP: ?", id="lbl-public-ip")

    def on_mount(self) -> None:
        table = self.query_one("#scan-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Port", "Status")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-ping":
            await self.run_ping()
        elif event.button.id == "btn-scan":
            await self.run_scan()
        elif event.button.id == "btn-dns":
            await self.run_dns()
        elif event.button.id == "btn-http":
            await self.run_http()
        elif event.button.id == "btn-ip":
            await self.run_ip()

    async def run_ping(self) -> None:
        host = self.query_one("#ping-host", Input).value
        count_str = self.query_one("#ping-count", Input).value
        count = int(count_str) if count_str else 4

        if not host:
            self.notify("Host required.", severity="error")
            return

        log = self.query_one("#ping-log", RichLog)
        log.clear()
        log.write(f"Pinging {host} ({count} times)...")
        self.notify("Pinging...")

        success = await asyncio.to_thread(self.manager.ping, host, count)

        if success:
            log.write("[bold green]Ping Successful[/bold green]")
            self.notify("Ping successful.")
        else:
            log.write("[bold red]Ping Failed[/bold red]")
            self.notify("Ping failed.", severity="error")

    async def run_scan(self) -> None:
        host = self.query_one("#scan-host", Input).value
        ports_str = self.query_one("#scan-ports", Input).value

        if not host:
            self.notify("Host required.", severity="error")
            return

        ports = []
        if ports_str:
            parts = ports_str.split(',')
            for part in parts:
                if '-' in part:
                    try:
                        start, end = map(int, part.split('-'))
                        ports.extend(range(start, end + 1))
                    except ValueError:
                        pass
                else:
                    try:
                        ports.append(int(part))
                    except ValueError:
                        pass
        else:
            # Default
            ports = [21, 22, 80, 443, 8000, 8080]

        table = self.query_one("#scan-table", DataTable)
        table.clear()
        self.notify(f"Scanning {len(ports)} ports on {host}...")

        results = await asyncio.to_thread(self.manager.scan_ports, host, ports)

        for port in sorted(results.keys()):
            status = results[port]
            color = "green" if status == "Open" else "red"
            table.add_row(str(port), f"[{color}]{status}[/{color}]")

        self.notify("Scan complete.")

    async def run_dns(self) -> None:
        domain = self.query_one("#dns-domain", Input).value
        rtype = self.query_one("#dns-type", Select).value

        if not domain:
            self.notify("Domain required.", severity="error")
            return

        log = self.query_one("#dns-log", RichLog)
        log.clear()
        log.write(f"Looking up {rtype} records for {domain}...")

        results = await asyncio.to_thread(self.manager.dns_lookup, domain, rtype)

        if "error" in results:
            log.write(f"[bold red]Error: {results['error']}[/bold red]")
        else:
            log.write(json.dumps(results, indent=2))

    async def run_http(self) -> None:
        url = self.query_one("#http-url", Input).value
        if not url:
            self.notify("URL required.", severity="error")
            return

        log = self.query_one("#http-log", RichLog)
        log.clear()
        log.write(f"Fetching HEAD for {url}...")

        result = await asyncio.to_thread(self.manager.http_head, url)

        if "error" in result:
            log.write(f"[bold red]Error: {result['error']}[/bold red]")
        else:
            log.write(f"Status: {result['status_code']}")
            log.write("[bold]Headers:[/bold]")
            for k, v in result['headers'].items():
                log.write(f"  {k}: {v}")

    async def run_ip(self) -> None:
        self.notify("Fetching IP info...")
        info = await asyncio.to_thread(self.manager.get_ip_info)

        self.query_one("#lbl-local-ip", Label).update(f"Local IP: [bold green]{info.get('local_ip')}[/bold green]")
        self.query_one("#lbl-public-ip", Label).update(f"Public IP: [bold green]{info.get('public_ip')}[/bold green]")
