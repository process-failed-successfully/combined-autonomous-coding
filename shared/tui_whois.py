import asyncio
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Input, Button, Label, RichLog, Static
from textual.reactive import reactive
from shared.whois_lab import WhoisLabManager

class WhoisLabTab(Vertical):
    """TUI Tab for Whois Lab."""

    is_querying = reactive(False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.manager = WhoisLabManager()

    def compose(self) -> ComposeResult:
        yield Label("Whois Lab", classes="tab-title")
        yield Label("Perform WHOIS lookups and check domain availability.", classes="tab-description")

        with Horizontal(id="whois-inputs-container"):
            yield Input(placeholder="Domain (e.g., example.com)", id="whois-domain")
            yield Input(placeholder="Optional Server (e.g., whois.iana.org)", id="whois-server")
            yield Button("Lookup", id="btn-whois-lookup", variant="primary")
            yield Button("Check Availability", id="btn-whois-check", variant="success")

        yield Label("", id="whois-status")

        # Use RichLog to allow scrolling
        self.output_log = RichLog(id="whois-output-log", markup=True, highlight=True, wrap=True)
        yield self.output_log

    def watch_is_querying(self, is_querying: bool) -> None:
        """Update UI based on querying state."""
        self.query_one("#btn-whois-lookup", Button).disabled = is_querying
        self.query_one("#btn-whois-check", Button).disabled = is_querying
        self.query_one("#whois-domain", Input).disabled = is_querying
        self.query_one("#whois-server", Input).disabled = is_querying

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-whois-lookup":
            await self.action_lookup()
        elif event.button.id == "btn-whois-check":
            await self.action_check()

    async def action_lookup(self) -> None:
        domain = self.query_one("#whois-domain", Input).value.strip()
        server = self.query_one("#whois-server", Input).value.strip()

        if not domain:
            self.notify("Please enter a domain.", title="Error", severity="error")
            return

        self.is_querying = True
        status_lbl = self.query_one("#whois-status", Label)
        status_lbl.update(f"Looking up {domain}...")
        self.output_log.clear()

        # Run lookup in thread to not block UI
        result = await asyncio.to_thread(self.manager.lookup, domain, server if server else None)

        self.output_log.write(result)
        status_lbl.update(f"Lookup complete for {domain}.")
        self.is_querying = False

    async def action_check(self) -> None:
        domain = self.query_one("#whois-domain", Input).value.strip()

        if not domain:
            self.notify("Please enter a domain.", title="Error", severity="error")
            return

        self.is_querying = True
        status_lbl = self.query_one("#whois-status", Label)
        status_lbl.update(f"Checking availability for {domain}...")
        self.output_log.clear()

        # Run check in thread to not block UI
        result = await asyncio.to_thread(self.manager.check_availability, domain)

        if result["available"]:
            status_lbl.update(f"✅ Domain '{domain}' appears to be AVAILABLE.")
            self.notify(f"Domain '{domain}' appears to be AVAILABLE.", title="Whois Check", severity="information")
        else:
            status_lbl.update(f"❌ Domain '{domain}' appears to be TAKEN (or status unknown).")
            self.notify(f"Domain '{domain}' appears to be TAKEN.", title="Whois Check", severity="warning")

        self.output_log.write("\n--- Raw Output ---\n")
        self.output_log.write(result["output"])
        self.is_querying = False
