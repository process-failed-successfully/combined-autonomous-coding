from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Label, Input, TextArea, Button
from pathlib import Path
from shared.phonetic_lab import PhoneticLabManager

class PhoneticLabTab(Container):
    """Tab for Phonetic Lab."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = PhoneticLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Phonetic Lab (Soundex)[/bold]", classes="welcome-text")

            with Vertical(classes="stat-box"):
                yield Label("Input Text:")
                yield TextArea(id="phonetic-input")

            with Horizontal(classes="stat-box"):
                yield Button("Encode (Soundex)", id="btn-phonetic-soundex", variant="primary")
                yield Button("Clear", id="btn-phonetic-clear", variant="error")

            with Vertical(classes="stat-box"):
                yield Label("Output:")
                yield TextArea(id="phonetic-output", read_only=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-phonetic-soundex":
            self.action_encode()
        elif event.button.id == "btn-phonetic-clear":
            self.action_clear()

    def action_encode(self) -> None:
        input_text = self.query_one("#phonetic-input", TextArea).text
        output_area = self.query_one("#phonetic-output", TextArea)

        if not input_text.strip():
            output_area.text = ""
            return

        result = self.manager.soundex(input_text)
        output_area.text = result

    def action_clear(self) -> None:
        self.query_one("#phonetic-input", TextArea).text = ""
        self.query_one("#phonetic-output", TextArea).text = ""
