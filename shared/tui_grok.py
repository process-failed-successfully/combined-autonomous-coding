import json
from textual.app import ComposeResult
from textual.containers import VerticalScroll, Horizontal, Vertical
from textual.widgets import Static, Input, Button, Label, Pretty, Select
from textual.widgets import TabPane

from shared.grok_lab import GrokManager

class GrokLabTab(TabPane):
    """A Textual tab for parsing and testing Grok patterns."""

    def __init__(self, *args, **kwargs):
        super().__init__("Grok Lab", id="tab-grok", *args, **kwargs)
        self.manager = GrokManager()

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Static("Grok Pattern Tester", classes="header")

            with Vertical(classes="input-section"):
                yield Label("Grok Pattern:")
                yield Input(
                    placeholder="%{IP:client} %{WORD:method} %{URIPATHPARAM:request} %{NUMBER:bytes} %{NUMBER:duration}",
                    id="grok-pattern"
                )

                yield Label("Input Text:")
                yield Input(
                    placeholder="10.0.0.1 GET /index.html 15824 0.043",
                    id="grok-text"
                )

                yield Label("Or select a common pattern snippet to insert:")
                patterns = self.manager.get_patterns()
                yield Select(
                    [(f"%{{{p}}}", f"%{{{p}}}") for p in patterns],
                    prompt="Select a pattern snippet...",
                    id="grok-common-patterns"
                )

                with Horizontal():
                    yield Button("Parse", id="btn-parse-grok", variant="primary")
                    yield Button("Clear", id="btn-clear-grok", variant="default")

            yield Static("Extracted Data:", classes="header")
            yield Pretty({}, id="grok-result")
            yield Static("", id="grok-error", classes="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-parse-grok":
            self.parse_pattern()
        elif event.button.id == "btn-clear-grok":
            self.clear_inputs()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "grok-common-patterns" and event.select.value != Select.BLANK:
            pattern_input = self.query_one("#grok-pattern", Input)
            val = str(event.select.value)
            # Insert the selected snippet at the end
            current = pattern_input.value
            pattern_input.value = current + (" " if current else "") + val
            # Reset select
            event.select.value = Select.BLANK

    def parse_pattern(self) -> None:
        pattern = self.query_one("#grok-pattern", Input).value.strip()
        text = self.query_one("#grok-text", Input).value.strip()
        result_view = self.query_one("#grok-result", Pretty)
        error_view = self.query_one("#grok-error", Static)

        result_view.update({})
        error_view.update("")

        if not pattern:
            error_view.update("Please enter a Grok pattern.")
            return
        if not text:
            error_view.update("Please enter some input text.")
            return

        result = self.manager.parse(pattern, text)
        if result["success"]:
            result_view.update(result["match"])
        else:
            error_view.update(result["error"])

    def clear_inputs(self) -> None:
        self.query_one("#grok-pattern", Input).value = ""
        self.query_one("#grok-text", Input).value = ""
        self.query_one("#grok-result", Pretty).update({})
        self.query_one("#grok-error", Static).update("")
