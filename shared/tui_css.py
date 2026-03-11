from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Static, TextArea
from shared.css_lab import CssLabManager


class CssLabTab(Container):
    """TUI tab for CSS Lab utilities."""

    def compose(self) -> ComposeResult:
        with Horizontal(id="css-lab-header", classes="header-area"):
            yield Static("CSS Lab", classes="title")
            yield Static("Format and minify CSS", classes="subtitle")

        with Vertical(id="css-lab-content", classes="content-area"):
            yield Static("Input CSS:")
            self.input_area = TextArea(language="css", id="css-input")
            yield self.input_area

            with Horizontal(id="css-lab-controls", classes="button-group"):
                yield Button("Format", id="btn-format-css", variant="primary")
                yield Button("Minify", id="btn-minify-css", variant="warning")
                yield Button("Clear", id="btn-clear-css", variant="default")

            yield Static("Output:")
            self.output_area = TextArea(language="css", id="css-output", read_only=True)
            yield self.output_area

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        manager = CssLabManager()
        input_css = self.input_area.text

        if button_id == "btn-format-css":
            if input_css.strip():
                try:
                    formatted = manager.format(input_css)
                    self.output_area.text = formatted
                except Exception as e:
                    self.output_area.text = f"Error formatting CSS: {e}"
        elif button_id == "btn-minify-css":
            if input_css.strip():
                try:
                    minified = manager.minify(input_css)
                    self.output_area.text = minified
                except Exception as e:
                    self.output_area.text = f"Error minifying CSS: {e}"
        elif button_id == "btn-clear-css":
            self.input_area.text = ""
            self.output_area.text = ""
