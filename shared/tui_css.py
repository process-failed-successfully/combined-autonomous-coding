from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, TextArea
from shared.css_lab import CssLabManager

class CssLabTab(Container):
    """Tab for CSS Formatting/Minification."""

    DEFAULT_CSS = """
    CssLabTab {
        layout: vertical;
        height: 100%;
    }

    .css-box {
        height: auto;
        border: solid $accent;
        padding: 1;
        margin: 1;
    }

    #css-input, #css-output {
        height: 1fr;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.manager = CssLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]CSS Lab (Formatter/Minifier)[/bold]", classes="welcome-text")

            # Input Section
            with Vertical(classes="css-box"):
                yield Label("Input CSS:")
                yield TextArea(id="css-input", show_line_numbers=True, language="css")

            # Controls Section
            with Horizontal(classes="css-box"):
                yield Button("Format", id="btn-css-format", variant="primary")
                yield Button("Minify", id="btn-css-minify", variant="success")
                yield Button("Swap Input/Output", id="btn-css-swap", variant="warning")
                yield Button("Clear", id="btn-css-clear", variant="error")

            # Output Section
            with Vertical(classes="css-box"):
                yield Label("Output CSS:")
                yield TextArea(id="css-output", read_only=False, show_line_numbers=True, language="css")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-css-format":
            self.process(action="format")
        elif event.button.id == "btn-css-minify":
            self.process(action="minify")
        elif event.button.id == "btn-css-swap":
            self.swap_content()
        elif event.button.id == "btn-css-clear":
            self.clear_content()

    def process(self, action: str) -> None:
        text = self.query_one("#css-input", TextArea).text
        output_area = self.query_one("#css-output", TextArea)

        if not text:
            self.notify("Input is empty.", severity="warning")
            return

        try:
            if action == "format":
                result = self.manager.format(text)
            else:
                result = self.manager.minify(text)

            output_area.text = result
            self.notify("Done.")

        except Exception as e:
            output_area.text = f"Error: {e}"
            self.notify(f"Exception: {e}", severity="error")

    def swap_content(self) -> None:
        input_area = self.query_one("#css-input", TextArea)
        output_area = self.query_one("#css-output", TextArea)

        temp = input_area.text
        input_area.text = output_area.text
        output_area.text = temp
        self.notify("Swapped Input and Output.")

    def clear_content(self) -> None:
        self.query_one("#css-input", TextArea).text = ""
        self.query_one("#css-output", TextArea).text = ""
        self.notify("Cleared.")
