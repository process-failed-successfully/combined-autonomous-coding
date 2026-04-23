from textual.app import ComposeResult
from textual.widgets import Label, Button, Input, RichLog, TabbedContent, TabPane, Static
from textual.containers import Container, Horizontal, Vertical
from textual import on
from shared.ksuid_lab import KsuidLabManager

class KsuidLabTab(Container):
    """Tab for KSUID operations (Generate, Inspect)."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = KsuidLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]KSUID Lab[/bold]", classes="welcome-text")

            with TabbedContent():
                # Generate Tab
                with TabPane("Generate"):
                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Generate KSUIDs[/bold]")

                        with Horizontal():
                            yield Label("Count:")
                            yield Input(placeholder="1", id="input-ksuid-count", type="integer", value="1")

                        yield Button("Generate", id="btn-ksuid-generate", variant="primary")

                        yield Label("[bold]Output:[/bold]")
                        yield RichLog(id="log-ksuid-generate", wrap=True, highlight=True, markup=True)

                # Inspect Tab
                with TabPane("Inspect"):
                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Inspect KSUID[/bold]")
                        yield Input(placeholder="Enter KSUID to inspect", id="input-ksuid-inspect")
                        yield Button("Inspect", id="btn-ksuid-inspect", variant="primary")

                        yield Label("[bold]Inspection Result:[/bold]")
                        yield RichLog(id="log-ksuid-inspect", wrap=True, highlight=True, markup=True)

    @on(Button.Pressed, "#btn-ksuid-generate")
    def action_generate(self) -> None:
        count_input = self.query_one("#input-ksuid-count", Input).value
        log = self.query_one("#log-ksuid-generate", RichLog)

        try:
            count = int(count_input) if count_input else 1
        except ValueError:
            log.write("[bold red]Error: Count must be an integer.[/bold red]")
            return

        try:
            results = self.manager.generate(count=count)
            log.clear()
            for res in results:
                log.write(res)
        except Exception as e:
            log.write(f"[bold red]Error: {e}[/bold red]")

    @on(Button.Pressed, "#btn-ksuid-inspect")
    def action_inspect(self) -> None:
        ksuid_input = self.query_one("#input-ksuid-inspect", Input).value
        log = self.query_one("#log-ksuid-inspect", RichLog)
        log.clear()

        if not ksuid_input:
            log.write("[bold red]Please enter a KSUID to inspect.[/bold red]")
            return

        info = self.manager.inspect(ksuid_input)

        if not info["valid"]:
            log.write(f"[bold red]Error: {info['error']}[/bold red]")
            return

        log.write(f"[bold green]Valid KSUID[/bold green]")
        log.write(f"Timestamp:     {info['timestamp']}")
        if info.get("timestamp_iso"):
             log.write(f"Date (UTC):    {info['timestamp_iso']}")
        log.write(f"Payload (Hex): {info['payload_hex']}")
