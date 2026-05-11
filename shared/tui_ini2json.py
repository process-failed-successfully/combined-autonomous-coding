from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, TextArea, Button
from textual import on

from shared.ini2json_lab import Ini2JsonManager


class Ini2JsonLabTab(Container):
    """
    INI to JSON conversion tab.
    """
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = Ini2JsonManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]INI to JSON Converter[/bold]", classes="welcome-text")

            with Horizontal():
                with Vertical(classes="stat-box"):
                    yield Label("[bold]Input INI[/bold]")
                    yield TextArea(id="ini2json-input")
                    yield Button("Convert to JSON", id="btn-convert-ini2json", variant="primary")

                with Vertical(classes="stat-box"):
                    yield Label("[bold]Output JSON[/bold]")
                    yield TextArea(id="ini2json-output", read_only=True)

    @on(Button.Pressed, "#btn-convert-ini2json")
    def on_convert(self) -> None:
        ini_input = self.query_one("#ini2json-input", TextArea).text
        output_area = self.query_one("#ini2json-output", TextArea)

        if not ini_input.strip():
            self.notify("Please enter INI to convert.", severity="warning")
            return

        try:
            json_str = self.manager.convert(ini_input)
            output_area.text = json_str
            self.notify("Conversion successful.")
        except Exception as e:
            output_area.text = f"Error: {e}"
            self.notify("Conversion failed.", severity="error")
