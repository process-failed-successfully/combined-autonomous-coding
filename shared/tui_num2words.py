from textual.app import ComposeResult
from textual.widgets import Input, Static, TabPane
from textual.containers import Vertical
from shared.num2words_lab import Num2WordsManager

class TabNum2WordsLab(TabPane):
    """A TUI tab for converting numbers to words."""

    def __init__(self, **kwargs):
        super().__init__("Num2Words", id="tab-num2words-lab", **kwargs)
        self.manager = Num2WordsManager()

    def compose(self) -> ComposeResult:
        with Vertical(classes="container p-2"):
            yield Static("Enter a number to convert to English words:", classes="mb-1")
            yield Input(placeholder="e.g. 12345", id="num2words-input")

            yield Static("Result:", classes="mt-2 mb-1")
            yield Static("", id="num2words-output", classes="output-area p-2 border-solid border-primary")

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "num2words-input":
            self.convert_number(event.value)

    def convert_number(self, value: str) -> None:
        output_widget = self.query_one("#num2words-output", Static)

        value = value.strip()
        if not value:
            output_widget.update("")
            return

        try:
            result = self.manager.convert(value)
            output_widget.update(result)
            output_widget.remove_class("text-error")
        except ValueError as e:
            output_widget.update(f"Error: {e}")
            output_widget.add_class("text-error")
