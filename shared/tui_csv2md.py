import asyncio
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Input, Button, Label, TextArea

from shared.csv2md_lab import Csv2MdManager

class Csv2MdTab(Vertical):
    """A tab for converting CSV to Markdown tables."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.manager = Csv2MdManager()
        self.auto_convert_task: Optional[asyncio.Task] = None

    def compose(self) -> ComposeResult:
        with Vertical(classes="pl-content-container"):
            yield Static("CSV to Markdown Lab", classes="pl-tab-title")

            yield Static("Enter CSV text to convert it dynamically into a Markdown table.", classes="pl-description")

            with Horizontal(id="csv2md-controls"):
                self.delimiter_input = Input(
                    placeholder="Delimiter (e.g. , or ;)",
                    id="csv2md-delimiter",
                    classes="pl-input",
                    value=","
                )
                yield self.delimiter_input
                yield Button("Convert", id="btn-csv2md-convert", variant="primary")

            with Vertical(id="csv2md-input-container"):
                yield Label("CSV Input:", classes="pl-result-label")
                self.csv_input = TextArea(
                    id="csv2md-textarea",
                    language="markdown"
                )
                yield self.csv_input

            with Vertical(id="csv2md-result-container", classes="pl-result-panel"):
                yield Label("Markdown Table Output:", classes="pl-result-label")
                self.result_textarea = TextArea(
                    "",
                    id="csv2md-result-textarea",
                    language="markdown"
                )
                yield self.result_textarea

                self.error_label = Label("", id="csv2md-error-text", classes="pl-error")
                yield self.error_label

    def on_mount(self) -> None:
        self.csv_input.focus()

    async def on_text_area_changed(self, event: TextArea.Changed) -> None:
        """Handle dynamic conversion with a slight debounce."""
        if event.text_area.id == "csv2md-textarea":
            if self.auto_convert_task:
                self.auto_convert_task.cancel()
            self.auto_convert_task = asyncio.create_task(self._delayed_convert())

    async def on_input_changed(self, event: Input.Changed) -> None:
        """Handle delimiter change with a slight debounce."""
        if event.input.id == "csv2md-delimiter":
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
        if event.button.id == "btn-csv2md-convert":
            self.convert_input()

    def convert_input(self) -> None:
        """Performs the conversion logic."""
        csv_data = self.csv_input.text.strip()
        delimiter = self.delimiter_input.value or ","

        if not csv_data:
            self.result_textarea.text = ""
            self.error_label.update("")
            return

        try:
            output = self.manager.convert_to_markdown(csv_data, delimiter=delimiter)
            self.result_textarea.text = output
            self.error_label.update("")
        except Exception as e:
            self.result_textarea.text = ""
            self.error_label.update(str(e))
