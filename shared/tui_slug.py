from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, Input
import pyperclip

from shared.slug_lab import SlugManager

class SlugLabTab(Container):
    """Tab for String Slugification."""

    DEFAULT_CSS = """
    SlugLabTab {
        layout: vertical;
        height: 100%;
        overflow-y: auto;
    }

    .slug-box {
        height: auto;
        border: solid $accent;
        padding: 1;
        margin: 1;
    }

    .slug-output-label {
        margin-top: 1;
        text-style: bold;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = SlugManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Slug Lab (String Slugifier)[/bold]", classes="welcome-text")

            with Vertical(classes="slug-box"):
                yield Label("String to Slugify:")
                yield Input(placeholder="Enter string (e.g., Hello World! Âñtëññà)", id="slug-input")

                with Horizontal():
                    yield Button("Generate Slug", id="btn-slug-generate", variant="primary")
                    yield Button("Copy", id="btn-slug-copy", variant="success")

                yield Label("Result:", classes="slug-output-label")
                yield Input(id="slug-output", disabled=True)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-slug-generate":
            self.generate_slug()
        elif event.button.id == "btn-slug-copy":
            self.copy_to_clipboard()

    def generate_slug(self) -> None:
        input_widget = self.query_one("#slug-input", Input)
        output_widget = self.query_one("#slug-output", Input)

        text = input_widget.value.strip()

        if not text:
            output_widget.value = ""
            return

        result = self.manager.generate_slug(text)
        output_widget.value = result

    def copy_to_clipboard(self) -> None:
        output_widget = self.query_one("#slug-output", Input)
        text = output_widget.value
        if text:
            try:
                pyperclip.copy(text)
                self.app.notify("Copied to clipboard!", severity="information")
            except Exception as e:
                self.app.notify(f"Clipboard error: {e}", severity="error")
        else:
            self.app.notify("Nothing to copy.", severity="warning")
