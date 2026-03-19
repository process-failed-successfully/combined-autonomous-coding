from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import TabPane, Label, Input, Button, Static, Select, Switch
from shared.lorem_lab import LoremLabManager
import pyperclip

class LoremLabTab(TabPane):
    """Tab pane for generating Lorem Ipsum text."""

    def __init__(self, *args, **kwargs):
        super().__init__("Lorem Lab", id="tab-lorem", *args, **kwargs)
        self.manager = LoremLabManager()

    def compose(self) -> ComposeResult:
        with Vertical(classes="p-4"):
            yield Label("Lorem Ipsum Generator", classes="text-xl text-primary mb-4")

            with Horizontal(classes="mb-4 h-auto items-center"):
                yield Label("Generate:", classes="w-24")
                yield Input(value="1", id="input-lorem-count", type="integer", classes="w-24 mr-4")
                yield Select(
                    [("Paragraphs", "paragraphs"), ("Sentences", "sentences"), ("Words", "words")],
                    value="paragraphs",
                    id="select-lorem-type",
                    classes="w-32 mr-4"
                )

                yield Label("Start with 'Lorem ipsum...'", classes="mr-2")
                yield Switch(value=True, id="switch-lorem-start", classes="mr-4")

            with Horizontal(classes="mb-4 h-auto"):
                yield Button("Generate", variant="primary", id="btn-generate-lorem", classes="mr-4")
                yield Button("Copy to Clipboard", variant="default", id="btn-copy-lorem")

            yield Label("Output:", classes="mb-2")
            yield Static("", id="static-lorem-output", classes="border border-panel p-2 h-1fr overflow-y-auto")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-generate-lorem":
            try:
                count_input = self.query_one("#input-lorem-count", Input)
                count = int(count_input.value or "1")
            except ValueError:
                count = 1

            type_select = self.query_one("#select-lorem-type", Select)
            text_type = type_select.value

            start_switch = self.query_one("#switch-lorem-start", Switch)
            start_with_lorem = start_switch.value

            output = ""
            if text_type == "paragraphs":
                output = self.manager.generate_paragraphs(count, start_with_lorem)
            elif text_type == "sentences":
                output = self.manager.generate_sentences(count, start_with_lorem)
            elif text_type == "words":
                output = self.manager.generate_words(count, start_with_lorem)

            output_static = self.query_one("#static-lorem-output", Static)
            output_static.update(output)

        elif event.button.id == "btn-copy-lorem":
            output_static = self.query_one("#static-lorem-output", Static)
            content = str(output_static.render())
            if content:
                try:
                    pyperclip.copy(content)
                    if hasattr(self.app, 'notify'):
                        self.app.notify("Copied to clipboard!", title="Success")
                except Exception as e:
                    if hasattr(self.app, 'notify'):
                        self.app.notify(f"Failed to copy: {e}", title="Error", severity="error")
