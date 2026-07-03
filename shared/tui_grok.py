from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Label, Button, TextArea, Input
from textual.containers import ScrollableContainer
import json

from shared.grok_lab import GrokManager

class GrokLabTab(ScrollableContainer):
    """TUI Tab for Grok Lab."""

    def __init__(self, project_dir=None, **kwargs):
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = GrokManager()

    def compose(self) -> ComposeResult:
        with Vertical(classes="tab-content"):
            yield Label("[bold]Grok Lab[/bold] - Interactive Grok Pattern Parser", classes="tab-title")

            with Horizontal(classes="action-bar"):
                yield Button("Parse", id="btn-grok-parse", variant="primary")
                yield Button("Clear", id="btn-grok-clear", variant="warning")

            with Vertical(classes="panel"):
                yield Label("Grok Pattern (e.g., %{IP:client} %{WORD:method}):")
                yield Input(id="grok-pattern-input", placeholder="Enter Grok pattern...")

                yield Label("Input Text:")
                yield TextArea(id="grok-text-input", language="text", text="")

            with Vertical(classes="panel"):
                yield Label("Parsed Output / Error:")
                yield TextArea(id="grok-output-area", language="json", read_only=True)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-grok-parse":
            self.parse_grok()
        elif event.button.id == "btn-grok-clear":
            self.clear_all()

    def parse_grok(self) -> None:
        pattern = self.query_one("#grok-pattern-input", Input).value.strip()
        text = self.query_one("#grok-text-input", TextArea).text.strip()
        output_area = self.query_one("#grok-output-area", TextArea)

        if not pattern:
            self.app.notify("Grok pattern is required.", severity="error")
            return

        if not text:
            self.app.notify("Input text is required.", severity="error")
            return

        result = self.manager.parse(pattern, text)
        if result["success"]:
            output_area.text = json.dumps(result["fields"], indent=2)
            self.app.notify("Parse successful.")
        else:
            output_area.text = json.dumps({"error": result["error"]}, indent=2)
            self.app.notify("Parse failed.", severity="error")

    def clear_all(self) -> None:
        self.query_one("#grok-pattern-input", Input).value = ""
        self.query_one("#grok-text-input", TextArea).text = ""
        self.query_one("#grok-output-area", TextArea).text = ""
        self.app.notify("Fields cleared.")
