from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, TextArea, Button
from textual import on

from shared.entropy_lab import EntropyLabManager


class EntropyLabTab(Container):
    """Tab for Entropy Lab."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = EntropyLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Entropy Lab[/bold]", classes="welcome-text")

            with Horizontal(classes="stat-box"):
                yield Button("Analyze Text", id="btn-entropy-analyze", variant="primary")
                yield Button("Clear", id="btn-entropy-clear", variant="warning")

            with Horizontal():
                with Vertical(classes="stat-box"):
                    yield Label("[bold]Input Text[/bold]")
                    yield TextArea(id="entropy-input-text")

                with Vertical(classes="stat-box"):
                    yield Label("[bold]Analysis Output[/bold]")
                    yield TextArea(id="entropy-output-text", read_only=True)

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        input_area = self.query_one("#entropy-input-text", TextArea)
        output_area = self.query_one("#entropy-output-text", TextArea)

        if event.button.id == "btn-entropy-analyze":
            text = input_area.text
            if not text:
                self.notify("Input required.", severity="error")
                return

            data = text.encode("utf-8")
            result = self.manager.analyze_data(data)

            output = f"Size: {result['length']} bytes\n"
            output += f"Entropy: {result['entropy']:.4f} bits per byte\n"
            output += f"Assessment: {result['assessment']}\n"

            output_area.text = output
            self.notify("Entropy analyzed.")

        elif event.button.id == "btn-entropy-clear":
            input_area.text = ""
            output_area.text = ""
            self.notify("Cleared.")
