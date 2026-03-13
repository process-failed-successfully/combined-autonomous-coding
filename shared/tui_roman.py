import asyncio
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Input, Button, Label

from shared.roman_lab import RomanLabManager

class RomanLabTab(Vertical):
    """A tab for Roman numeral conversions."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.manager = RomanLabManager()
        self.auto_convert_task: Optional[asyncio.Task] = None

    def compose(self) -> ComposeResult:
        with Vertical(classes="pl-content-container"):
            yield Static("Roman Numeral Lab", classes="pl-tab-title")

            yield Static("Enter an integer or Roman numeral to convert it dynamically.", classes="pl-description")

            with Horizontal(id="roman-input-container"):
                self.input_field = Input(
                    placeholder="e.g. 2024 or MMXXIV",
                    id="roman-input",
                    classes="pl-input"
                )
                yield self.input_field

                yield Button("Convert", id="btn-roman-convert", variant="primary")

            with Vertical(id="roman-result-container", classes="pl-result-panel"):
                yield Label("Result:", classes="pl-result-label")
                self.result_label = Label("", id="roman-result-text")
                yield self.result_label

                self.error_label = Label("", id="roman-error-text", classes="pl-error")
                yield self.error_label

    def on_mount(self) -> None:
        self.input_field.focus()

    async def on_input_changed(self, event: Input.Changed) -> None:
        """Handle dynamic conversion with a slight debounce."""
        if event.input.id == "roman-input":
            if self.auto_convert_task:
                self.auto_convert_task.cancel()
            self.auto_convert_task = asyncio.create_task(self._delayed_convert())

    async def _delayed_convert(self) -> None:
        """Debounce input before processing conversion."""
        try:
            await asyncio.sleep(0.3)
            self.convert_input()
        except asyncio.CancelledError:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-roman-convert":
            self.convert_input()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "roman-input":
            self.convert_input()

    def convert_input(self) -> None:
        """Performs the conversion logic."""
        val = self.input_field.value.strip()

        if not val:
            self.result_label.update("")
            self.error_label.update("")
            return

        success, output = self.manager.convert(val)

        if success:
            self.result_label.update(output)
            self.error_label.update("")
        else:
            self.result_label.update("")
            self.error_label.update(output)
