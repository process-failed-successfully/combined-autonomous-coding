from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll, Horizontal
from textual.widgets import Input, Button, RichLog, TabbedContent, TabPane
from textual import on
from shared.cidr_lab import CidrLabManager
import json

class CidrLabTab(Container):
    """TUI for CIDR Lab."""

    def __init__(self):
        super().__init__()
        self.manager = CidrLabManager()

    def compose(self) -> ComposeResult:
        with TabbedContent(initial="cidr-tab-info"):
            # Info Tab
            with TabPane("Info", id="cidr-tab-info"):
                with VerticalScroll():
                    yield Input(placeholder="CIDR block (e.g. 192.168.1.0/24)", id="cidr-info-input")
                    with Horizontal():
                        yield Button("Get Info", id="btn-cidr-info", variant="primary")
                        yield Button("Clear", id="btn-cidr-info-clear")
                    yield RichLog(id="cidr-info-log", wrap=True, highlight=True, markup=True)

            # Contains Tab
            with TabPane("Contains", id="cidr-tab-contains"):
                with VerticalScroll():
                    yield Input(placeholder="Container CIDR", id="cidr-contains-container")
                    yield Input(placeholder="Target IP or CIDR", id="cidr-contains-target")
                    with Horizontal():
                        yield Button("Check Contains", id="btn-cidr-contains", variant="primary")
                        yield Button("Clear", id="btn-cidr-contains-clear")
                    yield RichLog(id="cidr-contains-log", wrap=True, highlight=True, markup=True)

            # Overlaps Tab
            with TabPane("Overlaps", id="cidr-tab-overlaps"):
                with VerticalScroll():
                    yield Input(placeholder="First CIDR", id="cidr-overlaps-1")
                    yield Input(placeholder="Second CIDR", id="cidr-overlaps-2")
                    with Horizontal():
                        yield Button("Check Overlaps", id="btn-cidr-overlaps", variant="primary")
                        yield Button("Clear", id="btn-cidr-overlaps-clear")
                    yield RichLog(id="cidr-overlaps-log", wrap=True, highlight=True, markup=True)

            # Subnet Tab
            with TabPane("Subnet", id="cidr-tab-subnet"):
                with VerticalScroll():
                    yield Input(placeholder="Base CIDR", id="cidr-subnet-base")
                    yield Input(placeholder="New prefix length (integer)", id="cidr-subnet-prefix")
                    with Horizontal():
                        yield Button("Subnet", id="btn-cidr-subnet", variant="primary")
                        yield Button("Clear", id="btn-cidr-subnet-clear")
                    yield RichLog(id="cidr-subnet-log", wrap=True, highlight=True, markup=True)

    @on(Button.Pressed, "#btn-cidr-info")
    def action_info(self, event: Button.Pressed) -> None:
        log = self.query_one("#cidr-info-log", RichLog)
        cidr = self.query_one("#cidr-info-input", Input).value.strip()

        if not cidr:
            log.write("[red]Error: Please provide a CIDR block.[/red]")
            return

        result = self.manager.get_info(cidr)
        if "error" in result:
            from textual.markup import escape
            log.write(f"[red]Error: {escape(result['error'])}[/red]")
        else:
            log.write(f"[green]--- Network Info: {result['cidr']} ---[/green]")
            for k, v in result.items():
                if k == "cidr": continue
                key_display = k.replace("_", " ").title()
                log.write(f"  [bold]{key_display:<20}:[/bold] {v}")
            log.write("\n")

    @on(Button.Pressed, "#btn-cidr-info-clear")
    def action_info_clear(self, event: Button.Pressed) -> None:
        self.query_one("#cidr-info-input", Input).value = ""
        self.query_one("#cidr-info-log", RichLog).clear()

    @on(Button.Pressed, "#btn-cidr-contains")
    def action_contains(self, event: Button.Pressed) -> None:
        log = self.query_one("#cidr-contains-log", RichLog)
        container = self.query_one("#cidr-contains-container", Input).value.strip()
        target = self.query_one("#cidr-contains-target", Input).value.strip()

        if not container or not target:
            log.write("[red]Error: Please provide both Container CIDR and Target IP/CIDR.[/red]")
            return

        result = self.manager.contains(container, target)
        if "error" in result:
            from textual.markup import escape
            log.write(f"[red]Error: {escape(result['error'])}[/red]")
        else:
            emoji = "✅" if result["contains"] else "❌"
            msg = "contains" if result["contains"] else "does NOT contain"
            color = "green" if result["contains"] else "yellow"
            log.write(f"[{color}]{emoji} Network {result['container']} {msg} {result['type']} {result['target']}[/{color}]\n")

    @on(Button.Pressed, "#btn-cidr-contains-clear")
    def action_contains_clear(self, event: Button.Pressed) -> None:
        self.query_one("#cidr-contains-container", Input).value = ""
        self.query_one("#cidr-contains-target", Input).value = ""
        self.query_one("#cidr-contains-log", RichLog).clear()

    @on(Button.Pressed, "#btn-cidr-overlaps")
    def action_overlaps(self, event: Button.Pressed) -> None:
        log = self.query_one("#cidr-overlaps-log", RichLog)
        cidr1 = self.query_one("#cidr-overlaps-1", Input).value.strip()
        cidr2 = self.query_one("#cidr-overlaps-2", Input).value.strip()

        if not cidr1 or not cidr2:
            log.write("[red]Error: Please provide both CIDRs.[/red]")
            return

        result = self.manager.overlaps(cidr1, cidr2)
        if "error" in result:
            from textual.markup import escape
            log.write(f"[red]Error: {escape(result['error'])}[/red]")
        else:
            emoji = "⚠️ " if result["overlaps"] else "✅"
            msg = "OVERLAP" if result["overlaps"] else "do not overlap"
            color = "red" if result["overlaps"] else "green"
            log.write(f"[{color}]{emoji} {result['cidr1']} and {result['cidr2']} {msg}.[/{color}]\n")

    @on(Button.Pressed, "#btn-cidr-overlaps-clear")
    def action_overlaps_clear(self, event: Button.Pressed) -> None:
        self.query_one("#cidr-overlaps-1", Input).value = ""
        self.query_one("#cidr-overlaps-2", Input).value = ""
        self.query_one("#cidr-overlaps-log", RichLog).clear()

    @on(Button.Pressed, "#btn-cidr-subnet")
    def action_subnet(self, event: Button.Pressed) -> None:
        log = self.query_one("#cidr-subnet-log", RichLog)
        cidr = self.query_one("#cidr-subnet-base", Input).value.strip()
        prefix_str = self.query_one("#cidr-subnet-prefix", Input).value.strip()

        if not cidr or not prefix_str:
            log.write("[red]Error: Please provide both Base CIDR and New prefix length.[/red]")
            return

        try:
            prefix = int(prefix_str)
        except ValueError:
            log.write("[red]Error: Prefix length must be an integer.[/red]")
            return

        result = self.manager.subnet(cidr, prefix)
        if "error" in result:
            from textual.markup import escape
            log.write(f"[red]Error: {escape(result['error'])}[/red]")
        else:
            log.write(f"[green]--- Subnetting {result['cidr']} to /{result['new_prefix']} ---[/green]")
            log.write(f"[bold]Total Subnets:[/bold] {result['count']}")
            log.write("[bold]Subnets:[/bold]")
            for s in result["subnets"]:
                log.write(f"  - {s}")
            log.write("\n")

    @on(Button.Pressed, "#btn-cidr-subnet-clear")
    def action_subnet_clear(self, event: Button.Pressed) -> None:
        self.query_one("#cidr-subnet-base", Input).value = ""
        self.query_one("#cidr-subnet-prefix", Input).value = ""
        self.query_one("#cidr-subnet-log", RichLog).clear()
