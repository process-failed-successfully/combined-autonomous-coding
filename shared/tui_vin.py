from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Label, Button, Input, RichLog
from textual import on
from shared.vin_lab import VinManager

class VinLabTab(Container):
    """Tab for validating and decoding Vehicle Identification Numbers (VINs)."""

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]VIN Lab[/bold]", classes="welcome-text")

            with Vertical(classes="stat-box"):
                yield Label("Enter VIN:")
                yield Input(placeholder="e74c3c...", id="vin-input")

                with Vertical(classes="action-buttons"):
                    yield Button("Validate VIN", id="btn-vin-validate", variant="primary")
                    yield Button("Decode VIN", id="btn-vin-decode", variant="success")

                yield RichLog(id="vin-result", wrap=True, highlight=True, markup=True)

    @on(Button.Pressed, "#btn-vin-validate")
    def on_validate(self) -> None:
        vin_str = self.query_one("#vin-input", Input).value
        log = self.query_one("#vin-result", RichLog)
        log.clear()

        if not vin_str:
            log.write("[bold red]Please enter a VIN.[/bold red]")
            return

        manager = VinManager()
        is_valid = manager.validate(vin_str)

        if is_valid:
            log.write(f"✅ The VIN '[bold cyan]{vin_str}[/bold cyan]' is valid (checksum verified).")
        else:
            log.write(f"❌ The VIN '[bold red]{vin_str}[/bold red]' is INVALID.")

    @on(Button.Pressed, "#btn-vin-decode")
    def on_decode(self) -> None:
        vin_str = self.query_one("#vin-input", Input).value
        log = self.query_one("#vin-result", RichLog)
        log.clear()

        if not vin_str:
            log.write("[bold red]Please enter a VIN.[/bold red]")
            return

        manager = VinManager()
        try:
            decoded = manager.decode(vin_str)

            log.write(f"[bold cyan]VIN:[/bold cyan] {decoded['vin']}")
            log.write(f"[bold]Valid:[/bold] {'[green]Yes[/green]' if decoded['is_valid'] else '[red]No[/red]'}")
            log.write(f"[bold]Region:[/bold] {decoded['region']}")
            log.write(f"[bold]WMI (World Manufacturer Identifier):[/bold] {decoded['wmi']}")
            log.write(f"[bold]VDS (Vehicle Descriptor Section):[/bold] {decoded['vds']}")
            log.write(f"[bold]VIS (Vehicle Identifier Section):[/bold] {decoded['vis']}")
            log.write(f"[bold]Estimated Year:[/bold] {decoded['year']}")
            log.write(f"[bold]Plant Code:[/bold] {decoded['plant_code']}")
            log.write(f"[bold]Serial Number:[/bold] {decoded['serial_number']}")

        except ValueError as e:
            log.write(f"[bold red]Error: {e}[/bold red]")
