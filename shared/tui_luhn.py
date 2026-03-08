from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, Input
from shared.luhn_lab import LuhnManager

class LuhnLabTab(Container):
    """Tab for Luhn Lab Operations."""

    DEFAULT_CSS = """
    LuhnLabTab {
        layout: vertical;
        height: 100%;
        overflow-y: auto;
    }

    .luhn-box {
        height: auto;
        border: solid $accent;
        padding: 1;
        margin: 1;
    }

    .luhn-output-label {
        margin-top: 1;
        text-style: bold;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = LuhnManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Luhn Lab (Validator/Generator)[/bold]", classes="welcome-text")

            # Validate Section
            with Vertical(classes="luhn-box"):
                yield Label("Validate Number:")
                with Horizontal():
                    yield Input(placeholder="Enter number to validate...", id="luhn-validate-input")
                    yield Button("Validate", id="btn-luhn-validate", variant="primary")
                yield Label("", id="luhn-validate-output", classes="luhn-output-label")

            # Generate Section
            with Vertical(classes="luhn-box"):
                yield Label("Generate Number:")
                with Horizontal():
                    yield Input(placeholder="Length (e.g. 16)", id="luhn-generate-length", type="integer")
                    yield Input(placeholder="Prefix (optional)", id="luhn-generate-prefix")
                    yield Button("Generate", id="btn-luhn-generate", variant="success")
                yield Label("", id="luhn-generate-output", classes="luhn-output-label")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-luhn-validate":
            self.validate_number()
        elif event.button.id == "btn-luhn-generate":
            self.generate_number()

    def validate_number(self) -> None:
        input_widget = self.query_one("#luhn-validate-input", Input)
        output_label = self.query_one("#luhn-validate-output", Label)
        number = input_widget.value.strip()

        if not number:
            output_label.update("[red]Please enter a number.[/red]")
            return

        is_valid = self.manager.validate(number)
        if is_valid:
            output_label.update(f"[green]✅ '{number}' is a valid Luhn sequence.[/green]")
        else:
            output_label.update(f"[red]❌ '{number}' is INVALID.[/red]")

    def generate_number(self) -> None:
        length_input = self.query_one("#luhn-generate-length", Input)
        prefix_input = self.query_one("#luhn-generate-prefix", Input)
        output_label = self.query_one("#luhn-generate-output", Label)

        length_str = length_input.value.strip()
        prefix = prefix_input.value.strip()

        if not length_str:
            output_label.update("[red]Please specify a length.[/red]")
            return

        try:
            length = int(length_str)
        except ValueError:
            output_label.update("[red]Length must be an integer.[/red]")
            return

        try:
            generated = self.manager.generate(length=length, prefix=prefix)
            output_label.update(f"[green]✅ Generated: {generated}[/green]")
        except ValueError as e:
            output_label.update(f"[red]❌ Error: {e}[/red]")
