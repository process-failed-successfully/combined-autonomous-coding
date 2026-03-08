from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, Input
from shared.iban_lab import IbanManager

class IbanLabTab(Container):
    """Tab for IBAN Lab Operations."""

    DEFAULT_CSS = """
    IbanLabTab {
        layout: vertical;
        height: 100%;
        overflow-y: auto;
    }

    .iban-box {
        height: auto;
        border: solid $accent;
        padding: 1;
        margin: 1;
    }

    .iban-output-label {
        margin-top: 1;
        text-style: bold;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = IbanManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]IBAN Lab (Validator/Generator/Parser)[/bold]", classes="welcome-text")

            # Validate Section
            with Vertical(classes="iban-box"):
                yield Label("Validate IBAN:")
                with Horizontal():
                    yield Input(placeholder="Enter IBAN to validate...", id="iban-validate-input")
                    yield Button("Validate", id="btn-iban-validate", variant="primary")
                yield Label("", id="iban-validate-output", classes="iban-output-label")

            # Generate Section
            with Vertical(classes="iban-box"):
                yield Label("Generate IBAN:")
                with Horizontal():
                    yield Input(placeholder="Country Code (e.g. DE, GB, FR)", id="iban-generate-country")
                    yield Button("Generate", id="btn-iban-generate", variant="success")
                yield Label("", id="iban-generate-output", classes="iban-output-label")

            # Parse Section
            with Vertical(classes="iban-box"):
                yield Label("Parse IBAN:")
                with Horizontal():
                    yield Input(placeholder="Enter IBAN to parse...", id="iban-parse-input")
                    yield Button("Parse", id="btn-iban-parse", variant="warning")
                yield Label("", id="iban-parse-output", classes="iban-output-label")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-iban-validate":
            self.validate_iban()
        elif event.button.id == "btn-iban-generate":
            self.generate_iban()
        elif event.button.id == "btn-iban-parse":
            self.parse_iban()

    def validate_iban(self) -> None:
        input_widget = self.query_one("#iban-validate-input", Input)
        output_label = self.query_one("#iban-validate-output", Label)
        iban = input_widget.value.strip()

        if not iban:
            output_label.update("[red]Please enter an IBAN.[/red]")
            return

        is_valid = self.manager.validate(iban)
        if is_valid:
            output_label.update(f"[green]✅ '{iban}' is a valid IBAN.[/green]")
        else:
            output_label.update(f"[red]❌ '{iban}' is INVALID.[/red]")

    def generate_iban(self) -> None:
        country_input = self.query_one("#iban-generate-country", Input)
        output_label = self.query_one("#iban-generate-output", Label)

        country_code = country_input.value.strip().upper()

        if not country_code:
            output_label.update("[red]Please specify a country code.[/red]")
            return

        try:
            generated = self.manager.generate(country_code=country_code)
            output_label.update(f"[green]✅ Generated: {generated}[/green]")
        except ValueError as e:
            output_label.update(f"[red]❌ Error: {e}[/red]")

    def parse_iban(self) -> None:
        input_widget = self.query_one("#iban-parse-input", Input)
        output_label = self.query_one("#iban-parse-output", Label)
        iban = input_widget.value.strip()

        if not iban:
            output_label.update("[red]Please enter an IBAN.[/red]")
            return

        try:
            parsed = self.manager.parse(iban)
            is_valid_str = "Yes" if parsed['is_valid'] else "No"
            output_text = (
                f"IBAN: {parsed['iban']}\n"
                f"Country Code: {parsed['country_code']}\n"
                f"Checksum: {parsed['checksum']}\n"
                f"BBAN: {parsed['bban']}\n"
                f"Valid: {is_valid_str}"
            )
            output_label.update(f"[green]{output_text}[/green]")
        except ValueError as e:
            output_label.update(f"[red]❌ Error: {e}[/red]")
