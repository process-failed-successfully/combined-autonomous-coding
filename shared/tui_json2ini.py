from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, TextArea, Button
from textual import on

from shared.json2ini_lab import Json2IniManager


class Json2IniLabTab(Container):
    """
    JSON to INI conversion tab.
    """
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = Json2IniManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]JSON to INI Converter[/bold]", classes="welcome-text")

            with Horizontal():
                with Vertical(classes="stat-box"):
                    yield Label("[bold]Input JSON[/bold]")
                    yield TextArea(id="json2ini-input")
                    yield Button("Convert to INI", id="btn-convert-json2ini", variant="primary")

                with Vertical(classes="stat-box"):
                    yield Label("[bold]Output INI[/bold]")
                    yield TextArea(id="json2ini-output", read_only=True)

    @on(Button.Pressed, "#btn-convert-json2ini")
    def on_convert(self) -> None:
        json_input = self.query_one("#json2ini-input", TextArea).text
        output_area = self.query_one("#json2ini-output", TextArea)

        if not json_input.strip():
            self.notify("Please enter JSON to convert.", severity="warning")
            return

        try:
            ini_str = self.manager.convert(json_input)
            output_area.text = ini_str
            self.notify("Conversion successful.")
        except Exception as e:
            output_area.text = f"Error: {e}"
            self.notify("Conversion failed.", severity="error")
