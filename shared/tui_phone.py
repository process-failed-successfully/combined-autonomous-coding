from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Label, Button, Input, Select, RichLog
from textual import on, work

try:
    from shared.phone_lab import PhoneLabManager, PHONENUMBERS_AVAILABLE
except ImportError:
    PHONENUMBERS_AVAILABLE = False


class PhoneLabTab(Container):
    """Tab for Phone Lab operations."""

    def compose(self) -> ComposeResult:
        if not PHONENUMBERS_AVAILABLE:
            yield Label("[bold red]The 'phonenumbers' library is required for Phone Lab.[/bold red]\nPlease install it using: pip install phonenumbers")
            return

        with Vertical():
            yield Label("[bold]Phone Lab[/bold]", classes="welcome-text")

            with Vertical(classes="stat-box"):
                yield Label("Phone Number:")
                yield Input(placeholder="e.g., +1 415-555-2671 or 415-555-2671", id="phone-input")

                yield Label("Default Region (Optional, e.g., US, GB):")
                yield Input(placeholder="e.g., US", id="phone-region")

                with Horizontal():
                    yield Button("Parse & Info", id="btn-phone-info", variant="primary")
                    yield Button("Validate", id="btn-phone-validate", variant="primary")

                yield RichLog(id="phone-result", wrap=True, highlight=False, markup=True)

    @on(Button.Pressed, "#btn-phone-info")
    def on_info(self) -> None:
        try:
            manager = PhoneLabManager()
        except ImportError as e:
            log = self.query_one("#phone-result", RichLog)
            log.write(f"[bold red]Error: {e}[/bold red]")
            return

        phone = self.query_one("#phone-input", Input).value
        region = self.query_one("#phone-region", Input).value or None
        log = self.query_one("#phone-result", RichLog)
        log.clear()

        if not phone:
            log.write("[bold red]Error: Please provide a phone number[/bold red]")
            return

        try:
            info = manager.get_info(phone, region)

            log.write(f"[bold cyan]--- Phone Lookup: {phone} ---[/bold cyan]")

            if info.get('valid') or info.get('possible'):
                log.write(f"  Valid: [{'green' if info['valid'] else 'red'}]{info['valid']}[/]")
                log.write(f"  Possible: [{'green' if info['possible'] else 'yellow'}]{info['possible']}[/]")
                log.write(f"  Country Code: +{info['country_code']}")
                log.write(f"  National Number: {info['national_number']}")
                if info.get("extension"):
                    log.write(f"  Extension: {info['extension']}")

                log.write("\n[bold]Formats:[/bold]")
                log.write(f"  E164: {info['e164']}")
                log.write(f"  International: {info['international']}")
                log.write(f"  National: {info['national']}")
                log.write(f"  RFC3966: {info['rfc3966']}")

            if info.get("valid"):
                log.write("\n[bold]Details:[/bold]")
                log.write(f"  Type: {info['type']}")
                log.write(f"  Region Code: {info['region_code']}")
                if info.get("location"):
                    log.write(f"  Location: {info['location']}")
                if info.get("carrier"):
                    log.write(f"  Carrier: {info['carrier']}")
                if info.get("timezones"):
                    log.write(f"  Timezones: {', '.join(info['timezones'])}")

            if not info.get("valid") and not info.get("possible"):
                log.write("[bold red]The provided phone number is invalid and not possible.[/bold red]")

        except ValueError as e:
            log.write(f"[bold red]Error: {e}[/bold red]")

    @on(Button.Pressed, "#btn-phone-validate")
    def on_validate(self) -> None:
        try:
            manager = PhoneLabManager()
        except ImportError as e:
            log = self.query_one("#phone-result", RichLog)
            log.write(f"[bold red]Error: {e}[/bold red]")
            return

        phone = self.query_one("#phone-input", Input).value
        region = self.query_one("#phone-region", Input).value or None
        log = self.query_one("#phone-result", RichLog)
        log.clear()

        if not phone:
            log.write("[bold red]Error: Please provide a phone number[/bold red]")
            return

        is_valid = manager.is_valid(phone, region)
        if is_valid:
            log.write(f"[bold green]✅ Valid Phone Number: {phone}[/bold green]")
        else:
            log.write(f"[bold red]❌ Invalid Phone Number: {phone}[/bold red]")
