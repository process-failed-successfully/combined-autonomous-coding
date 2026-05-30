from textual.app import ComposeResult
from textual.widgets import Label, TextArea
from textual.containers import Vertical, Horizontal
from textual import on
from shared.atbash_lab import atbash_cipher


class AtbashLabTab(Vertical):
    """Tab for experimenting with the Atbash cipher."""

    def compose(self) -> ComposeResult:
        yield Label("[bold]Atbash Lab[/bold]", classes="welcome-text")

        with Horizontal(classes="stat-box"):
            with Vertical():
                yield Label("Input Text:")
                yield TextArea(id="atbash-input", language=None)
            with Vertical():
                yield Label("Atbash Output:")
                yield TextArea(id="atbash-output", read_only=True, language=None)

    @on(TextArea.Changed, "#atbash-input")
    def on_input_changed(self) -> None:
        input_text = self.query_one("#atbash-input", TextArea).text
        output_area = self.query_one("#atbash-output", TextArea)

        if not input_text:
            output_area.text = ""
            return

        output_area.text = atbash_cipher(input_text)
