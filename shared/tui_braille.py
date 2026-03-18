from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Label, TextArea, Button
from textual import on

from shared.braille_lab import BrailleLabManager


class BrailleLabTab(Vertical):
    """TUI tab for Braille encoding and decoding."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.manager = BrailleLabManager()
        self._updating = False

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("Text (English)", classes="section-label"),
            TextArea(id="braille-text-input", show_line_numbers=False),
            Horizontal(
                Button("Clear", id="braille-clear-btn", variant="error")
            ),
            Label("Braille", classes="section-label"),
            TextArea(id="braille-output", show_line_numbers=False),
            id="braille-container"
        )

    def on_mount(self) -> None:
        self.query_one("#braille-text-input", TextArea).focus()

    @on(TextArea.Changed, "#braille-text-input")
    def on_text_changed(self, event: TextArea.Changed) -> None:
        if self._updating:
            return
        self._updating = True
        try:
            braille_area = self.query_one("#braille-output", TextArea)
            braille_area.text = self.manager.encode(event.text_area.text)
        finally:
            self._updating = False

    @on(TextArea.Changed, "#braille-output")
    def on_braille_changed(self, event: TextArea.Changed) -> None:
        if self._updating:
            return
        self._updating = True
        try:
            text_area = self.query_one("#braille-text-input", TextArea)
            text_area.text = self.manager.decode(event.text_area.text)
        finally:
            self._updating = False

    @on(Button.Pressed, "#braille-clear-btn")
    def on_clear(self, event: Button.Pressed) -> None:
        self._updating = True
        try:
            self.query_one("#braille-text-input", TextArea).text = ""
            self.query_one("#braille-output", TextArea).text = ""
        finally:
            self._updating = False
