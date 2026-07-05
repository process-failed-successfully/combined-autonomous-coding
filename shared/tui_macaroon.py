from textual import work
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import TabPane, Label, Input, Button, RichLog
from textual.binding import Binding

from shared.macaroon_lab import MacaroonManager


class MacaroonLabTab(TabPane):
    """TUI Tab for Macaroon Lab."""

    BINDINGS = [
        Binding("escape", "clear_log", "Clear Log", show=True),
    ]

    def __init__(self, *args, **kwargs):
        # Memory explicit rule: Yield directly in TabbedContent if subclassing TabPane.
        super().__init__("Macaroon Lab", id="tab-macaroon", *args, **kwargs)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("Macaroon Lab", classes="header-label")

            with Horizontal(classes="stat-box"):
                with Vertical():
                    yield Label("Generate Macaroon")
                    yield Input(placeholder="Location (e.g., http://mybank/)", id="macaroon-gen-loc")
                    yield Input(placeholder="Identifier (e.g., user123)", id="macaroon-gen-id")
                    yield Input(placeholder="Secret Key", id="macaroon-gen-key", password=True)
                    yield Button("Generate", id="btn-macaroon-gen", variant="success")

                with Vertical():
                    yield Label("Inspect / Add Caveat")
                    yield Input(placeholder="Token (Base64 URL encoded)", id="macaroon-token")
                    yield Button("Inspect", id="btn-macaroon-inspect", variant="primary")
                    yield Input(placeholder="First Party Caveat (e.g., time < 2024-01-01)", id="macaroon-caveat")
                    yield Button("Add Caveat", id="btn-macaroon-caveat", variant="warning")

            with Vertical(classes="stat-box"):
                yield Label("Verify Macaroon")
                yield Input(placeholder="Secret Key (for verification)", id="macaroon-ver-key", password=True)
                yield Input(placeholder="Satisfy Caveats (comma separated, e.g., time < 2024-01-01)", id="macaroon-ver-caveats")
                yield Button("Verify", id="btn-macaroon-verify", variant="error")

            yield Label("Output:")
            yield RichLog(id="macaroon-log", wrap=True, highlight=True, markup=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-macaroon-gen":
            self.action_generate()
        elif event.button.id == "btn-macaroon-inspect":
            self.action_inspect()
        elif event.button.id == "btn-macaroon-caveat":
            self.action_caveat()
        elif event.button.id == "btn-macaroon-verify":
            self.action_verify()

    def action_clear_log(self) -> None:
        log = self.query_one("#macaroon-log", RichLog)
        log.clear()

    @work
    async def action_generate(self) -> None:
        loc = self.query_one("#macaroon-gen-loc", Input).value
        identifier = self.query_one("#macaroon-gen-id", Input).value
        key = self.query_one("#macaroon-gen-key", Input).value
        log = self.query_one("#macaroon-log", RichLog)

        if not loc or not identifier or not key:
            log.write("[bold red]Location, Identifier, and Secret Key are required to generate.[/bold red]")
            return

        res = MacaroonManager.generate(loc, identifier, key)
        if res["success"]:
            log.write("[bold green]Generated Macaroon:[/bold green]")
            log.write(res["token"])
            # Auto-fill token input for convenience
            self.query_one("#macaroon-token", Input).value = res["token"]
        else:
            log.write(f"[bold red]Error:[/bold red] {res['error']}")

    @work
    async def action_inspect(self) -> None:
        token = self.query_one("#macaroon-token", Input).value
        log = self.query_one("#macaroon-log", RichLog)

        if not token:
            log.write("[bold red]Token is required to inspect.[/bold red]")
            return

        res = MacaroonManager.inspect(token)
        if res["success"]:
            log.write("[bold green]Macaroon Inspection:[/bold green]")
            log.write(f"[bold cyan]Location:[/bold cyan] {res['location']}")
            log.write(f"[bold cyan]Identifier:[/bold cyan] {res['identifier']}")
            log.write(f"[bold cyan]Signature:[/bold cyan] {res['signature']}")
            log.write("[bold cyan]Caveats:[/bold cyan]")
            if res['caveats']:
                for c in res['caveats']:
                    log.write(f"  - {c}")
            else:
                log.write("  None")
        else:
            log.write(f"[bold red]Error:[/bold red] {res['error']}")

    @work
    async def action_caveat(self) -> None:
        token = self.query_one("#macaroon-token", Input).value
        caveat = self.query_one("#macaroon-caveat", Input).value
        log = self.query_one("#macaroon-log", RichLog)

        if not token or not caveat:
            log.write("[bold red]Token and Caveat are required to add a caveat.[/bold red]")
            return

        res = MacaroonManager.add_caveat(token, caveat)
        if res["success"]:
            log.write("[bold green]Macaroon Updated (Caveat Added):[/bold green]")
            log.write(res["token"])
            self.query_one("#macaroon-token", Input).value = res["token"]
            self.query_one("#macaroon-caveat", Input).value = ""
        else:
            log.write(f"[bold red]Error:[/bold red] {res['error']}")

    @work
    async def action_verify(self) -> None:
        token = self.query_one("#macaroon-token", Input).value
        key = self.query_one("#macaroon-ver-key", Input).value
        caveats_str = self.query_one("#macaroon-ver-caveats", Input).value
        log = self.query_one("#macaroon-log", RichLog)

        if not token or not key:
            log.write("[bold red]Token and Secret Key are required to verify.[/bold red]")
            return

        caveats = [c.strip() for c in caveats_str.split(",")] if caveats_str else []
        res = MacaroonManager.verify(token, key, caveats)

        if res["success"]:
            log.write(f"[bold green]{res['message']}[/bold green]")
        else:
            log.write(f"[bold red]Verification Failed:[/bold red] {res['error']}")
