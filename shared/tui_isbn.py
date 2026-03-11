from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, Input, Select
from shared.isbn_lab import IsbnManager

class IsbnLabTab(Container):
    """Tab for ISBN Lab Operations."""

    DEFAULT_CSS = """
    IsbnLabTab {
        layout: vertical;
        height: 100%;
        overflow-y: auto;
    }

    .isbn-box {
        height: auto;
        border: solid $accent;
        padding: 1;
        margin: 1;
    }

    .isbn-output-label {
        margin-top: 1;
        text-style: bold;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = IsbnManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]ISBN Lab (Validator/Generator/Parser/Converter)[/bold]", classes="welcome-text")

            # Validate Section
            with Vertical(classes="isbn-box"):
                yield Label("Validate ISBN:")
                with Horizontal():
                    yield Input(placeholder="Enter ISBN-10 or ISBN-13...", id="isbn-validate-input")
                    yield Button("Validate", id="btn-isbn-validate", variant="primary")
                yield Label("", id="isbn-validate-output", classes="isbn-output-label")

            # Generate Section
            with Vertical(classes="isbn-box"):
                yield Label("Generate ISBN:")
                with Horizontal():
                    yield Select.from_values(["10", "13"], id="isbn-generate-format", value="13")
                    yield Input(placeholder="Prefix (978 or 979 for ISBN-13)", id="isbn-generate-prefix", value="978")
                    yield Button("Generate", id="btn-isbn-generate", variant="success")
                yield Label("", id="isbn-generate-output", classes="isbn-output-label")

            # Parse Section
            with Vertical(classes="isbn-box"):
                yield Label("Parse ISBN:")
                with Horizontal():
                    yield Input(placeholder="Enter ISBN to parse...", id="isbn-parse-input")
                    yield Button("Parse", id="btn-isbn-parse", variant="warning")
                yield Label("", id="isbn-parse-output", classes="isbn-output-label")

            # Convert Section
            with Vertical(classes="isbn-box"):
                yield Label("Convert ISBN-10 to ISBN-13:")
                with Horizontal():
                    yield Input(placeholder="Enter ISBN-10...", id="isbn-convert-input")
                    yield Button("Convert", id="btn-isbn-convert", variant="primary")
                yield Label("", id="isbn-convert-output", classes="isbn-output-label")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-isbn-validate":
            self.validate_isbn()
        elif event.button.id == "btn-isbn-generate":
            self.generate_isbn()
        elif event.button.id == "btn-isbn-parse":
            self.parse_isbn()
        elif event.button.id == "btn-isbn-convert":
            self.convert_isbn()

    def validate_isbn(self) -> None:
        input_widget = self.query_one("#isbn-validate-input", Input)
        output_label = self.query_one("#isbn-validate-output", Label)
        isbn = input_widget.value.strip()

        if not isbn:
            output_label.update("[red]Please enter an ISBN.[/red]")
            return

        is_valid = self.manager.validate(isbn)
        if is_valid:
            output_label.update(f"[green]✅ '{isbn}' is a valid ISBN.[/green]")
        else:
            output_label.update(f"[red]❌ '{isbn}' is INVALID.[/red]")

    def generate_isbn(self) -> None:
        format_select = self.query_one("#isbn-generate-format", Select)
        prefix_input = self.query_one("#isbn-generate-prefix", Input)
        output_label = self.query_one("#isbn-generate-output", Label)

        format_type = format_select.value
        prefix = prefix_input.value.strip() if format_type == "13" else ""

        try:
            generated = self.manager.generate(format_type=format_type, prefix=prefix)
            output_label.update(f"[green]✅ Generated ISBN-{format_type}: {generated}[/green]")
        except ValueError as e:
            output_label.update(f"[red]❌ Error: {e}[/red]")

    def parse_isbn(self) -> None:
        input_widget = self.query_one("#isbn-parse-input", Input)
        output_label = self.query_one("#isbn-parse-output", Label)
        isbn = input_widget.value.strip()

        if not isbn:
            output_label.update("[red]Please enter an ISBN.[/red]")
            return

        try:
            parsed = self.manager.parse(isbn)
            valid_str = "[green]Yes[/green]" if parsed['is_valid'] else "[red]No[/red]"

            output_text = (
                f"Format: {parsed['format']}\n"
                f"Clean ISBN: {parsed['clean_isbn']}\n"
            )
            if 'prefix' in parsed:
                output_text += f"Prefix: {parsed['prefix']}\n"

            output_text += (
                f"Registration Group: {parsed['registration_group']}\n"
                f"Registrant: {parsed['registrant']}\n"
                f"Publication: {parsed['publication']}\n"
                f"Checksum: {parsed['checksum']}\n"
                f"Valid: {valid_str}"
            )
            output_label.update(output_text)
        except ValueError as e:
            output_label.update(f"[red]❌ Error: {e}[/red]")

    def convert_isbn(self) -> None:
        input_widget = self.query_one("#isbn-convert-input", Input)
        output_label = self.query_one("#isbn-convert-output", Label)
        isbn = input_widget.value.strip()

        if not isbn:
            output_label.update("[red]Please enter an ISBN-10.[/red]")
            return

        try:
            converted = self.manager.convert(isbn)
            output_label.update(f"[green]✅ Converted to ISBN-13: {converted}[/green]")
        except ValueError as e:
            output_label.update(f"[red]❌ Error: {e}[/red]")
