from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, TextArea
from shared.slug_lab import SlugManager


class SlugLabTab(Container):
    """Tab for Slug generation."""

    DEFAULT_CSS = """
    SlugLabTab {
        layout: vertical;
        height: 100%;
    }

    .slug-box {
        height: auto;
        border: solid $accent;
        padding: 1;
        margin: 1;
    }

    #slug-input, #slug-output {
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Slug Lab (URL-friendly string generator)[/bold]", classes="welcome-text")

            # Input Section
            with Vertical(classes="slug-box"):
                yield Label("Input Text:")
                yield TextArea(id="slug-input", show_line_numbers=False)

            # Controls Section
            with Horizontal(classes="slug-box"):
                yield Button("Slugify", id="btn-slugify", variant="primary")
                yield Button("Clear", id="btn-slug-clear", variant="error")

            # Output Section
            with Vertical(classes="slug-box"):
                yield Label("Output Slug:")
                yield TextArea(id="slug-output", read_only=False, show_line_numbers=False)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-slugify":
            self.process_slug()
        elif event.button.id == "btn-slug-clear":
            self.clear_content()

    def process_slug(self) -> None:
        text = self.query_one("#slug-input", TextArea).text
        output_area = self.query_one("#slug-output", TextArea)

        if not text:
            self.notify("Input is empty.", severity="warning")
            return

        try:
            manager = SlugManager()
            result = manager.slugify(text)
            output_area.text = result
            self.notify("Done.")

        except Exception as e:
            output_area.text = f"Error: {e}"
            self.notify(f"Exception: {e}", severity="error")

    def clear_content(self) -> None:
        self.query_one("#slug-input", TextArea).text = ""
        self.query_one("#slug-output", TextArea).text = ""
        self.notify("Cleared.")
