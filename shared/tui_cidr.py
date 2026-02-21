from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Input, Label, RichLog, TabbedContent, TabPane, DataTable
from pathlib import Path
from typing import Optional

from shared.cidr_lab import CidrLabManager

class CidrLabTab(Container):
    """Tab for CIDR and Subnet Calculator operations."""

    def __init__(self, project_dir: Optional[Path] = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = CidrLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]CIDR Lab[/bold]", classes="welcome-text")

            with TabbedContent():
                # Tab 1: CIDR Info
                with TabPane("CIDR Info"):
                    with Vertical(classes="stat-box"):
                        with Horizontal():
                            yield Label("CIDR:", classes="label")
                            yield Input(placeholder="e.g. 192.168.1.0/24", id="info-cidr")
                            yield Button("Get Info", id="btn-info", variant="primary")
                        yield DataTable(id="info-table")

                # Tab 2: Subnet Calculator
                with TabPane("Subnet Calculator"):
                    with Vertical(classes="stat-box"):
                        with Horizontal():
                            yield Label("CIDR:", classes="label")
                            yield Input(placeholder="e.g. 10.0.0.0/8", id="subnet-cidr")
                            yield Label("New Prefix:", classes="label")
                            yield Input(placeholder="e.g. 16", id="subnet-prefix", type="integer")
                            yield Button("Calculate", id="btn-subnet", variant="warning")
                        yield RichLog(id="subnet-log", wrap=True, highlight=True, markup=True)

                # Tab 3: Contains Check
                with TabPane("Contains Check"):
                    with Vertical(classes="stat-box"):
                        with Horizontal():
                            yield Label("Network:", classes="label")
                            yield Input(placeholder="e.g. 192.168.0.0/16", id="contains-cidr")
                            yield Label("Target:", classes="label")
                            yield Input(placeholder="e.g. 192.168.1.5", id="contains-target")
                            yield Button("Check", id="btn-contains", variant="success")
                        yield Label("", id="lbl-contains-result", classes="value")

                # Tab 4: Overlap Check
                with TabPane("Overlap Check"):
                    with Vertical(classes="stat-box"):
                        with Horizontal():
                            yield Label("CIDR 1:", classes="label")
                            yield Input(placeholder="e.g. 10.0.0.0/8", id="overlap-cidr1")
                            yield Label("CIDR 2:", classes="label")
                            yield Input(placeholder="e.g. 10.1.0.0/16", id="overlap-cidr2")
                            yield Button("Check Overlap", id="btn-overlap", variant="error")
                        yield Label("", id="lbl-overlap-result", classes="value")

    def on_mount(self) -> None:
        # Configure Info Table
        table = self.query_one("#info-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Property", "Value")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-info":
            await self.run_info()
        elif event.button.id == "btn-subnet":
            await self.run_subnet()
        elif event.button.id == "btn-contains":
            await self.run_contains()
        elif event.button.id == "btn-overlap":
            await self.run_overlap()

    async def run_info(self) -> None:
        cidr = self.query_one("#info-cidr", Input).value
        if not cidr:
            self.notify("CIDR required.", severity="error")
            return

        table = self.query_one("#info-table", DataTable)
        table.clear()

        import asyncio
        info = await asyncio.to_thread(self.manager.get_info, cidr)

        if "error" in info:
            self.notify(f"Error: {info['error']}", severity="error")
            return

        for k, v in info.items():
            key_display = k.replace("_", " ").title()
            table.add_row(key_display, str(v))

        self.notify("Info loaded.")

    async def run_subnet(self) -> None:
        cidr = self.query_one("#subnet-cidr", Input).value
        prefix_str = self.query_one("#subnet-prefix", Input).value

        if not cidr or not prefix_str:
            self.notify("CIDR and Prefix required.", severity="error")
            return

        try:
            prefix = int(prefix_str)
        except ValueError:
            self.notify("Prefix must be an integer.", severity="error")
            return

        log = self.query_one("#subnet-log", RichLog)
        log.clear()
        log.write(f"Calculating subnets for {cidr} with prefix /{prefix}...")

        import asyncio
        result = await asyncio.to_thread(self.manager.subnet, cidr, prefix)

        if "error" in result:
            log.write(f"[bold red]Error: {result['error']}[/bold red]")
            self.notify("Calculation failed.", severity="error")
        else:
            log.write(f"[bold green]Total Subnets: {result['count']}[/bold green]")
            for s in result["subnets"]:
                log.write(f"  - {s}")
            self.notify("Calculation complete.")

    async def run_contains(self) -> None:
        cidr = self.query_one("#contains-cidr", Input).value
        target = self.query_one("#contains-target", Input).value

        if not cidr or not target:
            self.notify("Network and Target required.", severity="error")
            return

        lbl = self.query_one("#lbl-contains-result", Label)
        lbl.update("Checking...")

        import asyncio
        result = await asyncio.to_thread(self.manager.contains, cidr, target)

        if "error" in result:
            lbl.update(f"[red]Error: {result['error']}[/red]")
        else:
            if result["contains"]:
                lbl.update(f"[bold green]YES[/bold green] - {result['container']} contains {result['target']}")
            else:
                lbl.update(f"[bold red]NO[/bold red] - {result['container']} does NOT contain {result['target']}")

    async def run_overlap(self) -> None:
        cidr1 = self.query_one("#overlap-cidr1", Input).value
        cidr2 = self.query_one("#overlap-cidr2", Input).value

        if not cidr1 or not cidr2:
            self.notify("Both CIDRs required.", severity="error")
            return

        lbl = self.query_one("#lbl-overlap-result", Label)
        lbl.update("Checking...")

        import asyncio
        result = await asyncio.to_thread(self.manager.overlaps, cidr1, cidr2)

        if "error" in result:
            lbl.update(f"[red]Error: {result['error']}[/red]")
        else:
            if result["overlaps"]:
                lbl.update(f"[bold red]OVERLAP DETECTED[/bold red] between {result['cidr1']} and {result['cidr2']}")
            else:
                lbl.update(f"[bold green]NO OVERLAP[/bold green]")
