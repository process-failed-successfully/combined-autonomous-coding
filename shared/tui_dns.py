import asyncio
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Input, Label, RichLog, Select, TabbedContent, TabPane, DataTable

from shared.dns_lab import DnsLabManager
from shared.whois_lab import WhoisLabManager


class DnsLabTab(Container):
    """Tab for DNS Operations (Lookup, Propagation, Whois)."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.dns_manager = DnsLabManager()
        self.whois_manager = WhoisLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]DNS Lab[/bold]", classes="welcome-text")

            with TabbedContent():
                # DNS Lookup Pane
                with TabPane("Lookup"):
                    with Vertical(classes="stat-box"):
                        with Horizontal():
                            yield Label("Domain:", classes="label")
                            yield Input(placeholder="e.g. example.com", id="dns-lookup-domain")
                            yield Label("Type:", classes="label")
                            yield Select.from_values(
                                ["A", "AAAA", "CNAME", "MX", "TXT", "NS", "SOA", "PTR", "CAA", "SRV"],
                                id="dns-lookup-type",
                                value="A"
                            )
                        with Horizontal():
                            yield Label("Server:", classes="label")
                            yield Select.from_values(
                                ["Default", "Google (8.8.8.8)", "Cloudflare (1.1.1.1)", "Quad9 (9.9.9.9)", "OpenDNS (208.67.222.222)"],
                                id="dns-lookup-server",
                                value="Default"
                            )
                            yield Button("Lookup", id="btn-dns-lookup", variant="primary")

                        yield RichLog(id="dns-lookup-log", wrap=True, highlight=True, markup=True)

                # DNS Propagation Pane
                with TabPane("Propagation"):
                    with Vertical(classes="stat-box"):
                        with Horizontal():
                            yield Label("Domain:", classes="label")
                            yield Input(placeholder="e.g. example.com", id="dns-prop-domain")
                            yield Label("Type:", classes="label")
                            yield Select.from_values(
                                ["A", "AAAA", "CNAME", "MX", "TXT", "NS", "SOA"],
                                id="dns-prop-type",
                                value="A"
                            )
                            yield Button("Check Propagation", id="btn-dns-prop", variant="warning")

                        yield DataTable(id="dns-prop-table")

                # Whois Pane
                with TabPane("Whois"):
                    with Vertical(classes="stat-box"):
                        with Horizontal():
                            yield Label("Domain:", classes="label")
                            yield Input(placeholder="e.g. example.com", id="whois-domain")
                            yield Button("Lookup", id="btn-whois-lookup", variant="primary")
                            yield Button("Check Availability", id="btn-whois-check", variant="success")

                        yield RichLog(id="whois-log", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        table = self.query_one("#dns-prop-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Provider", "Server", "Result", "Status")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-dns-lookup":
            await self.run_lookup()
        elif event.button.id == "btn-dns-prop":
            await self.run_propagation()
        elif event.button.id == "btn-whois-lookup":
            await self.run_whois(check_availability=False)
        elif event.button.id == "btn-whois-check":
            await self.run_whois(check_availability=True)

    async def run_lookup(self) -> None:
        domain = self.query_one("#dns-lookup-domain", Input).value
        rtype = self.query_one("#dns-lookup-type", Select).value
        server_val = self.query_one("#dns-lookup-server", Select).value

        if not domain:
            self.notify("Domain required.", severity="error")
            return

        server = None
        if server_val == "Google (8.8.8.8)":
            server = "8.8.8.8"
        elif server_val == "Cloudflare (1.1.1.1)":
            server = "1.1.1.1"
        elif server_val == "Quad9 (9.9.9.9)":
            server = "9.9.9.9"
        elif server_val == "OpenDNS (208.67.222.222)":
            server = "208.67.222.222"

        log = self.query_one("#dns-lookup-log", RichLog)
        log.clear()
        log.write(f"Looking up {rtype} for {domain} on {server or 'Default'}...")
        self.notify("Running lookup...")

        try:
            result = await asyncio.to_thread(self.dns_manager.lookup, domain, rtype, server)

            if "error" in result:
                log.write(f"[bold red]Error: {result['error']}[/bold red]")
                self.notify("Lookup failed.", severity="error")
            else:
                records = result.get("records", [])
                if not records:
                    log.write("[yellow]No records found.[/yellow]")
                else:
                    log.write("[bold green]Records found:[/bold green]")
                    for r in records:
                        log.write(f"  {r}")
        except Exception as e:
            log.write(f"[bold red]Exception: {e}[/bold red]")
            self.notify(f"Error: {e}", severity="error")

    async def run_propagation(self) -> None:
        domain = self.query_one("#dns-prop-domain", Input).value
        rtype = self.query_one("#dns-prop-type", Select).value

        if not domain:
            self.notify("Domain required.", severity="error")
            return

        table = self.query_one("#dns-prop-table", DataTable)
        table.clear()
        self.notify(f"Checking propagation for {domain}...")

        servers_ip = {
            "Google": "8.8.8.8",
            "Cloudflare": "1.1.1.1",
            "Quad9": "9.9.9.9",
            "OpenDNS": "208.67.222.222"
        }

        try:
            results = await asyncio.to_thread(self.dns_manager.check_propagation, domain, rtype)

            for provider, data in results.items():
                server_ip = servers_ip.get(provider, "")

                if isinstance(data, dict) and "error" in data:
                    result_str = data["error"]
                    status = "[red]Error[/red]"
                elif not data:
                    result_str = "(No records)"
                    status = "[yellow]Empty[/yellow]"
                else:
                    result_str = "\n".join(data)
                    status = "[green]OK[/green]"

                table.add_row(provider, server_ip, result_str, status)

            self.notify("Propagation check complete.")

        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    async def run_whois(self, check_availability: bool = False) -> None:
        domain = self.query_one("#whois-domain", Input).value

        if not domain:
            self.notify("Domain required.", severity="error")
            return

        log = self.query_one("#whois-log", RichLog)
        log.clear()

        action = "Checking availability" if check_availability else "Performing WHOIS lookup"
        log.write(f"{action} for {domain}...")
        self.notify(f"{action}...")

        try:
            if check_availability:
                result = await asyncio.to_thread(self.whois_manager.check_availability, domain)
                if result["available"]:
                    log.write(f"[bold green]AVAILABLE[/bold green]: {domain}")
                else:
                    log.write(f"[bold red]TAKEN / UNKNOWN[/bold red]: {domain}")

                log.write("\n[dim]--- Output snippet ---[/dim]")
                log.write(result["output"][:500] + "..." if len(result["output"]) > 500 else result["output"])
            else:
                output = await asyncio.to_thread(self.whois_manager.lookup, domain)
                log.write(output)

        except Exception as e:
            log.write(f"[bold red]Error: {e}[/bold red]")
            self.notify(f"Error: {e}", severity="error")
