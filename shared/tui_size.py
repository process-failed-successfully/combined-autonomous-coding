from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.widgets import Input, Button, Static, Label, Select
from textual import on
from shared.size_lab import parse_size, format_size

class SizeLabTab(VerticalScroll):
    """TUI Tab for Size Lab."""

    def compose(self) -> ComposeResult:
        yield Static("Size Format Lab", classes="tab-title")

        # Parse Section
        yield Static("Parse human-readable size to bytes (e.g., '1.5 GB')", classes="section-title")
        with Horizontal(classes="input-group"):
            yield Input(placeholder="e.g. 1.5 GB", id="input-parse-size", classes="input-field w-1-2")
            yield Button("Parse", id="btn-parse", variant="primary")
        yield Static("", id="output-parse", classes="output-area")

        # Format Section
        yield Static("Format bytes to human-readable string", classes="section-title mt-2")
        with Horizontal(classes="input-group"):
            yield Input(placeholder="e.g. 1500000000", id="input-format-bytes", classes="input-field w-1-2")
            yield Select(
                [("IEC (Binary, KiB)", "iec"), ("SI (Decimal, KB)", "si")],
                value="iec",
                id="select-format-type",
                classes="w-1-4"
            )
            yield Button("Format", id="btn-format", variant="primary")
        yield Static("", id="output-format", classes="output-area")

    @on(Button.Pressed, "#btn-parse")
    async def handle_parse(self, event: Button.Pressed) -> None:
        """Handles parsing a size string."""
        input_widget = self.query_one("#input-parse-size", Input)
        output_widget = self.query_one("#output-parse", Static)

        size_str = input_widget.value.strip()
        if not size_str:
            output_widget.update("[red]Error: Please enter a size string.[/red]")
            return

        res = parse_size(size_str)
        if res["success"]:
            output_widget.update(f"[green]Bytes: {res['bytes']}[/green]")
        else:
            output_widget.update(f"[red]Error: {res['error']}[/red]")

    @on(Button.Pressed, "#btn-format")
    async def handle_format(self, event: Button.Pressed) -> None:
        """Handles formatting bytes to string."""
        input_widget = self.query_one("#input-format-bytes", Input)
        select_widget = self.query_one("#select-format-type", Select)
        output_widget = self.query_one("#output-format", Static)

        bytes_str = input_widget.value.strip()
        if not bytes_str:
            output_widget.update("[red]Error: Please enter a byte value.[/red]")
            return

        try:
            bytes_val = int(bytes_str)
        except ValueError:
            output_widget.update("[red]Error: Bytes must be a valid integer.[/red]")
            return

        use_iec = select_widget.value == "iec"
        res = format_size(bytes_val, use_iec=use_iec)

        if res["success"]:
            output_widget.update(f"[green]Formatted: {res['formatted']}[/green]")
        else:
            output_widget.update(f"[red]Error: {res['error']}[/red]")

    @on(Input.Submitted, "#input-parse-size")
    async def on_parse_submitted(self, event: Input.Submitted) -> None:
        await self.handle_parse(None)

    @on(Input.Submitted, "#input-format-bytes")
    async def on_format_submitted(self, event: Input.Submitted) -> None:
        await self.handle_format(None)
