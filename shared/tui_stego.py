from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, Input
from shared.stego_lab import StegoManager


class StegoLabTab(Container):
    """Tab for Stego Lab Operations."""

    DEFAULT_CSS = """
    StegoLabTab {
        layout: vertical;
        height: 100%;
        overflow-y: auto;
    }

    .stego-box {
        height: auto;
        border: solid $accent;
        padding: 1;
        margin: 1;
    }

    .stego-output-label {
        margin-top: 1;
        text-style: bold;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        # Handle instantiation even if Pillow is missing (e.g. CI environments)
        try:
            self.manager = StegoManager()
        except ImportError:
            self.manager = None

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Stego Lab (LSB Steganography)[/bold]", classes="welcome-text")

            if self.manager is None:
                yield Label("[red]Error: The 'Pillow' library is required. Please install it to use Stego Lab.[/red]")
                return

            # Hide Section
            with Vertical(classes="stego-box"):
                yield Label("Hide Message in Image:")
                with Horizontal():
                    yield Input(placeholder="Image Path...", id="stego-hide-image")
                    yield Input(placeholder="Secret Message...", id="stego-hide-message")
                    yield Input(placeholder="Output Image Path...", id="stego-hide-output")
                yield Button("Hide", id="btn-stego-hide", variant="primary")
                yield Label("", id="stego-hide-result", classes="stego-output-label")

            # Extract Section
            with Vertical(classes="stego-box"):
                yield Label("Extract Message from Image:")
                with Horizontal():
                    yield Input(placeholder="Image Path...", id="stego-extract-image")
                    yield Button("Extract", id="btn-stego-extract", variant="success")
                yield Label("", id="stego-extract-result", classes="stego-output-label")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-stego-hide":
            self.hide_message()
        elif event.button.id == "btn-stego-extract":
            self.extract_message()

    def hide_message(self) -> None:
        image_input = self.query_one("#stego-hide-image", Input)
        message_input = self.query_one("#stego-hide-message", Input)
        output_input = self.query_one("#stego-hide-output", Input)
        result_label = self.query_one("#stego-hide-result", Label)

        image_path = image_input.value.strip()
        message = message_input.value.strip()
        output_path = output_input.value.strip()

        if not image_path or not message or not output_path:
            result_label.update("[red]Please fill in all fields (Image, Message, Output).[/red]")
            return

        try:
            self.manager.hide(image_path, message, output_path)
            result_label.update(f"[green]✅ Message hidden successfully in {output_path}[/green]")
        except Exception as e:
            result_label.update(f"[red]❌ Error: {e}[/red]")

    def extract_message(self) -> None:
        image_input = self.query_one("#stego-extract-image", Input)
        result_label = self.query_one("#stego-extract-result", Label)

        image_path = image_input.value.strip()

        if not image_path:
            result_label.update("[red]Please specify the image path.[/red]")
            return

        try:
            message = self.manager.extract(image_path)
            result_label.update(f"[green]✅ Extracted Message: {message}[/green]")
        except Exception as e:
            result_label.update(f"[red]❌ Error: {e}[/red]")
