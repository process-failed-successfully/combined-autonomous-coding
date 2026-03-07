from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Label, Button, Input, Select, TabbedContent, TabPane, RichLog
from textual import on, work
from shared.mac_lab import MacLabManager


class MacLabTab(Container):
    """Tab for MAC Lab operations."""

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]MAC Lab[/bold]", classes="welcome-text")

            with TabbedContent(id="mac-tabs"):
                with TabPane("Generate", id="mac-tab-generate"):
                    with Vertical(classes="stat-box"):
                        yield Label("Count:")
                        yield Input(placeholder="1", id="mac-gen-count", value="1", type="integer")
                        yield Label("Prefix (Optional OUI):")
                        yield Input(placeholder="e.g., 00:1A:2B", id="mac-gen-prefix")
                        yield Label("Format:")
                        yield Select.from_values(
                            ["colon", "hyphen", "dot", "plain"],
                            id="mac-gen-format", value="colon"
                        )
                        yield Button("Generate", id="btn-mac-generate", variant="primary")
                        yield RichLog(id="mac-gen-result", wrap=True, highlight=False, markup=True)

                with TabPane("Format", id="mac-tab-format"):
                    with Vertical(classes="stat-box"):
                        yield Label("MAC Address:")
                        yield Input(placeholder="e.g., 001122334455", id="mac-fmt-input")
                        yield Label("Target Format:")
                        yield Select.from_values(
                            ["colon", "hyphen", "dot", "plain"],
                            id="mac-fmt-format", value="colon"
                        )
                        yield Button("Format", id="btn-mac-format", variant="primary")
                        yield RichLog(id="mac-fmt-result", wrap=True, highlight=False, markup=True)

                with TabPane("Validate", id="mac-tab-validate"):
                    with Vertical(classes="stat-box"):
                        yield Label("MAC Address:")
                        yield Input(placeholder="e.g., 00:11:22:33:44:55", id="mac-val-input")
                        yield Button("Validate", id="btn-mac-validate", variant="primary")
                        yield RichLog(id="mac-val-result", wrap=True, highlight=False, markup=True)

                with TabPane("Lookup", id="mac-tab-lookup"):
                    with Vertical(classes="stat-box"):
                        yield Label("MAC Address:")
                        yield Input(placeholder="e.g., 00:1A:2B:3C:4D:5E", id="mac-lookup-input")
                        yield Button("Lookup Vendor", id="btn-mac-lookup", variant="primary")
                        yield RichLog(id="mac-lookup-result", wrap=True, highlight=False, markup=True)

    @on(Button.Pressed, "#btn-mac-generate")
    def on_generate(self) -> None:
        manager = MacLabManager()
        count_str = self.query_one("#mac-gen-count", Input).value
        prefix = self.query_one("#mac-gen-prefix", Input).value
        fmt = self.query_one("#mac-gen-format", Select).value or "colon"
        log = self.query_one("#mac-gen-result", RichLog)
        log.clear()

        try:
            count = int(count_str) if count_str else 1
            if count <= 0:
                raise ValueError("Count must be positive")
            results = manager.generate(count=count, prefix=prefix, format=fmt)
            for res in results:
                log.write(f"[bold green]{res}[/bold green]")
        except Exception as e:
            log.write(f"[bold red]Error: {e}[/bold red]")

    @on(Button.Pressed, "#btn-mac-format")
    def on_format(self) -> None:
        manager = MacLabManager()
        mac = self.query_one("#mac-fmt-input", Input).value
        fmt = self.query_one("#mac-fmt-format", Select).value or "colon"
        log = self.query_one("#mac-fmt-result", RichLog)
        log.clear()

        if not mac:
            log.write("[bold red]Error: Please provide a MAC address[/bold red]")
            return

        try:
            res = manager.format(mac, fmt)
            log.write(f"[bold green]{res}[/bold green]")
        except ValueError as e:
            log.write(f"[bold red]Error: {e}[/bold red]")

    @on(Button.Pressed, "#btn-mac-validate")
    def on_validate(self) -> None:
        manager = MacLabManager()
        mac = self.query_one("#mac-val-input", Input).value
        log = self.query_one("#mac-val-result", RichLog)
        log.clear()

        if not mac:
            log.write("[bold red]Error: Please provide a MAC address[/bold red]")
            return

        is_valid = manager.validate(mac)
        if is_valid:
            log.write(f"[bold green]✅ Valid MAC Address: {mac}[/bold green]")
        else:
            log.write(f"[bold red]❌ Invalid MAC Address: {mac}[/bold red]")

    @on(Button.Pressed, "#btn-mac-lookup")
    async def on_lookup(self) -> None:
        manager = MacLabManager()
        mac = self.query_one("#mac-lookup-input", Input).value
        log = self.query_one("#mac-lookup-result", RichLog)
        log.clear()

        if not mac:
            log.write("[bold red]Error: Please provide a MAC address[/bold red]")
            return

        log.write("[italic]Looking up vendor info...[/italic]")

        self._perform_lookup(manager, mac, log)

    @work(thread=True)
    def _perform_lookup(self, manager, mac, log) -> None:
        try:
            info = manager.lookup(mac)

            def update_ui():
                log.clear()
                if not info.get("valid"):
                    log.write(f"[bold red]Error: {info.get('error', 'Unknown error')}[/bold red]")
                    return

                log.write(f"[bold cyan]--- MAC Lookup: {info['mac']} ---[/bold cyan]")
                log.write(f"  Prefix: [yellow]{info['prefix']}[/yellow]")
                log.write(f"  Vendor: [green]{info['vendor']}[/green]")

                if info.get("country"):
                    log.write(f"  Country: {info['country']}")
                if info.get("address"):
                    log.write(f"  Address: {info['address']}")

                if "error" in info:
                    log.write(f"\n  [italic red]Note: {info['error']}[/italic red]")

            self.app.call_from_thread(update_ui)

        except Exception as e:
            def update_error():
                log.clear()
                log.write(f"[bold red]Lookup failed: {str(e)}[/bold red]")
            self.app.call_from_thread(update_error)
