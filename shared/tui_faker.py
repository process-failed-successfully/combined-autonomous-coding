from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Input, Label, RichLog, Select
import json

from shared.faker_lab import FakerLabManager


class FakerLabTab(Container):
    """Tab for Faker Lab generating fake data."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        try:
            self.manager = FakerLabManager()
        except ImportError:
            self.manager = None

    def compose(self) -> ComposeResult:
        if self.manager is None:
            yield Label("Faker library not installed. Please install it using 'pip install faker'.", classes="error-text")
            return

        with Vertical():
            yield Label("[bold]Faker Lab - Generate Fake Data[/bold]", classes="welcome-text")

            with Horizontal(classes="stat-box"):
                with Vertical():
                    yield Label("Category:")
                    yield Select.from_values(["person", "internet", "text", "credit_card"], id="faker-type", value="person")
                with Vertical():
                    yield Label("Locale:")
                    yield Input(placeholder="en_US", id="faker-locale", value="en_US")
                with Vertical():
                    yield Label("Count:")
                    yield Input(placeholder="1", id="faker-count", value="1", type="integer")

            yield Button("Generate", id="btn-faker-generate", variant="primary")

            with Vertical(classes="stat-box"):
                yield Label("[bold]Generated Output[/bold]")
                yield RichLog(id="faker-output-log", wrap=True, highlight=True, markup=True)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-faker-generate":
            self.generate_fake_data()

    def generate_fake_data(self) -> None:
        type_val = str(self.query_one("#faker-type", Select).value)
        locale = self.query_one("#faker-locale", Input).value or "en_US"
        count_str = self.query_one("#faker-count", Input).value or "1"
        output_log = self.query_one("#faker-output-log", RichLog)

        try:
            count = int(count_str)
            if count <= 0:
                raise ValueError("Count must be greater than 0")
        except ValueError:
            self.notify("Invalid count value. Using 1.", severity="warning")
            count = 1

        output_log.clear()

        # Update manager if locale changed
        if self.manager.locale != locale:
            self.manager = FakerLabManager(locale=locale)

        try:
            if type_val == "person":
                result = self.manager.generate_person(count)
                output_log.write(json.dumps(result, indent=2))
            elif type_val == "internet":
                result = self.manager.generate_internet(count)
                output_log.write(json.dumps(result, indent=2))
            elif type_val == "text":
                result = self.manager.generate_text(count)
                for i, text in enumerate(result):
                    output_log.write(f"--- Text {i+1} ---\n{text}\n")
            elif type_val == "credit_card":
                result = self.manager.generate_credit_card(count)
                output_log.write(json.dumps(result, indent=2))

            self.notify(f"Generated {count} {type_val} record(s).")
        except Exception as e:
            output_log.write(f"[bold red]Error generating data:[/bold red] {e}")
            self.notify("Error generating data.", severity="error")
