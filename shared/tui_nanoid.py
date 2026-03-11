from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.widgets import Button, Input, Label, Static, Select
from shared.nanoid_lab import NanoIDLabManager
from textual import work
import pyperclip

class NanoIDLab(Container):
    """TUI for NanoID Lab."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.manager = NanoIDLabManager()

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Label("NanoID Generator", classes="title")

            yield Label("Size (default: 21):")
            yield Input(id="nanoid-size-input", value="21", placeholder="Size of the ID")

            yield Label("Custom Alphabet (leave blank for default URL-safe):")
            yield Input(id="nanoid-alphabet-input", value="", placeholder="e.g. 0123456789abc")

            yield Label("Count (default: 1):")
            yield Input(id="nanoid-count-input", value="1", placeholder="Number of IDs to generate")

            with Horizontal():
                yield Button("Generate NanoID(s)", id="btn-generate-nanoid", variant="primary")
                yield Button("Copy to Clipboard", id="btn-copy-nanoid")

            yield Label("Output:")
            yield Static("", id="nanoid-output", classes="output-box")


    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "btn-generate-nanoid":
            size_str = self.query_one("#nanoid-size-input", Input).value
            alphabet = self.query_one("#nanoid-alphabet-input", Input).value
            count_str = self.query_one("#nanoid-count-input", Input).value

            try:
                size = int(size_str) if size_str.strip() else 21
                if size <= 0:
                    raise ValueError("Size must be positive.")
                count = int(count_str) if count_str.strip() else 1
                if count <= 0:
                    raise ValueError("Count must be positive.")

                alphabet = alphabet if alphabet.strip() else None

                self.generate_nanoids(size=size, alphabet=alphabet, count=count)
            except ValueError as e:
                self.query_one("#nanoid-output", Static).update(f"Error: {e}")

        elif button_id == "btn-copy-nanoid":
            output_text = self.query_one("#nanoid-output", Static).render()
            if output_text and not str(output_text).startswith("Error:"):
                pyperclip.copy(str(output_text))
                self.app.notify("Copied to clipboard!")

    @work(thread=True)
    def generate_nanoids(self, size: int, alphabet: str | None, count: int) -> None:
        try:
            results = self.manager.generate(count=count, size=size, alphabet=alphabet)
            result_str = "\n".join(results)
            self.app.call_from_thread(self._update_output, result_str)
        except Exception as e:
            self.app.call_from_thread(self._update_output, f"Error: {str(e)}")

    def _update_output(self, text: str) -> None:
        output_widget = self.query_one("#nanoid-output", Static)
        output_widget.update(text)
