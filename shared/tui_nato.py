from textual.app import ComposeResult
from textual.widgets import Label, Button, Input, TabbedContent, TabPane, TextArea
from textual.containers import Container, Horizontal, Vertical
from shared.nato_lab import NatoLabManager

class NatoLabTab(Container):
    """Tab for NATO Phonetic Alphabet operations."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = NatoLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]NATO Phonetic Alphabet Lab[/bold]", classes="welcome-text")

            with TabbedContent():
                # Encode Pane
                with TabPane("Encode"):
                    with Vertical(classes="stat-box"):
                        yield Label("Input Text:")
                        yield TextArea(id="nato-encode-input")

                        with Horizontal():
                            yield Button("Encode", id="btn-nato-encode", variant="primary")
                            yield Button("Clear", id="btn-nato-encode-clear", variant="default")

                        yield Label("[bold]NATO Phonetic Representation:[/bold]")
                        yield TextArea(id="nato-encode-result", read_only=True)

                # Decode Pane
                with TabPane("Decode"):
                    with Vertical(classes="stat-box"):
                        yield Label("Phonetic Text (e.g., Alfa Bravo Charlie):")
                        yield TextArea(id="nato-decode-input")

                        with Horizontal():
                            yield Button("Decode", id="btn-nato-decode", variant="primary")
                            yield Button("Clear", id="btn-nato-decode-clear", variant="default")

                        yield Label("[bold]Original Text:[/bold]")
                        yield TextArea(id="nato-decode-result", read_only=True)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-nato-encode":
            self.encode_text()
        elif event.button.id == "btn-nato-encode-clear":
            self.query_one("#nato-encode-input", TextArea).text = ""
            self.query_one("#nato-encode-result", TextArea).text = ""
        elif event.button.id == "btn-nato-decode":
            self.decode_text()
        elif event.button.id == "btn-nato-decode-clear":
            self.query_one("#nato-decode-input", TextArea).text = ""
            self.query_one("#nato-decode-result", TextArea).text = ""

    def encode_text(self) -> None:
        input_text = self.query_one("#nato-encode-input", TextArea).text
        if not input_text:
            self.notify("Please enter text to encode.", severity="warning")
            return

        try:
            result = self.manager.encode(input_text)
            self.query_one("#nato-encode-result", TextArea).text = result
            self.notify("Text encoded successfully.")
        except Exception as e:
            self.notify(f"Error encoding: {e}", severity="error")

    def decode_text(self) -> None:
        input_text = self.query_one("#nato-decode-input", TextArea).text
        if not input_text:
            self.notify("Please enter phonetic text to decode.", severity="warning")
            return

        try:
            result = self.manager.decode(input_text)
            self.query_one("#nato-decode-result", TextArea).text = result
            self.notify("Text decoded successfully.")
        except Exception as e:
            self.notify(f"Error decoding: {e}", severity="error")
