from textual.app import ComposeResult
from textual.widgets import Label, Button, Input, Static
from textual.containers import Container, Horizontal, Vertical
from textual import on

try:
    from shared.cuid2_lab import Cuid2LabManager, HAS_CUID2
except ImportError:
    HAS_CUID2 = False


class Cuid2LabTab(Container):
    """Tab for generating CUID2s."""

    def compose(self) -> ComposeResult:
        with Vertical(id="cuid2-container", classes="lab-container"):
            yield Label("[bold]CUID2 Lab[/bold]", classes="welcome-text")
            yield Label("Generate secure, collision-resistant ids optimized for horizontal scaling.", classes="subtitle")

            with Horizontal(id="cuid2-config"):
                with Vertical(classes="input-group"):
                    yield Label("Length (default 24):")
                    yield Input(id="cuid2-length", placeholder="24", type="number", value="24")

                with Vertical(classes="input-group"):
                    yield Label("Count:")
                    yield Input(id="cuid2-count", placeholder="1", type="integer", value="1")

            with Horizontal(id="cuid2-action"):
                yield Button("Generate", id="btn-cuid2-generate", variant="primary")

            yield Label("[bold]Output:[/bold]")
            yield Static("", id="cuid2-output", classes="output-box")

    def on_mount(self) -> None:
        if not HAS_CUID2:
            self.query_one("#cuid2-output", Static).update("Error: cuid2 library not installed. Please install it using 'pip install cuid2'.")

    @on(Button.Pressed, "#btn-cuid2-generate")
    def on_generate_pressed(self) -> None:
        if not HAS_CUID2:
            return

        try:
            manager = Cuid2LabManager()
        except ImportError as e:
            self.query_one("#cuid2-output", Static).update(f"Error: {e}")
            return

        length_str = self.query_one("#cuid2-length", Input).value
        count_str = self.query_one("#cuid2-count", Input).value

        try:
            length = int(length_str) if length_str.strip() else 24
            if length < 1:
                self.query_one("#cuid2-output", Static).update("Error: Length must be greater than 0.")
                return
        except ValueError:
            self.query_one("#cuid2-output", Static).update("Error: Length must be an integer.")
            return

        try:
            count = int(count_str) if count_str.strip() else 1
            if count < 1:
                self.query_one("#cuid2-output", Static).update("Error: Count must be greater than 0.")
                return
        except ValueError:
            self.query_one("#cuid2-output", Static).update("Error: Count must be an integer.")
            return

        try:
            results = manager.generate(count=count, length=length)
            formatted_results = "\n".join([f"[bold green]{r}[/bold green]" for r in results])
            self.query_one("#cuid2-output", Static).update(f"Generated CUID2(s):\n{formatted_results}")
        except Exception as e:
            self.query_one("#cuid2-output", Static).update(f"Error: {e}")
