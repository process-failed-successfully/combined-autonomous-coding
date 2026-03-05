from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static, Button, Label, TextArea, Select
from pathlib import Path

from shared.token_lab import TokenLabManager


class TokenLabTab(Container):
    """Textual Tab for Token Lab."""

    def __init__(self, project_dir: Path | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = TokenLabManager()

    def compose(self) -> ComposeResult:
        with Vertical(classes="tab-content"):
            yield Static("🪙 Token Lab", classes="tab-title")

            with Horizontal(id="token-controls"):
                yield Label("Encoding:", classes="field-label")
                yield Select(
                    [("cl100k_base (GPT-4/3.5)", "cl100k_base"),
                     ("p50k_base", "p50k_base"),
                     ("r50k_base", "r50k_base")],
                    value="cl100k_base",
                    id="token-encoding"
                )

            with Vertical(classes="card"):
                yield Label("Text to Encode:", classes="field-label")
                yield TextArea(id="token-input-text", classes="tall-input")

                with Horizontal():
                    yield Button("Count & Encode", id="btn-count", variant="primary")
                    yield Label("Tokens: 0", id="token-count-label", classes="status-label")

            with Vertical(classes="card"):
                yield Label("Encoded Tokens (comma-separated):", classes="field-label")
                yield TextArea(id="token-input-tokens", classes="tall-input")
                yield Button("Decode", id="btn-decode", variant="primary")

            with Vertical(classes="card"):
                yield Label("Output:", classes="field-label")
                yield TextArea(id="token-output", classes="tall-input", read_only=True)

    def on_mount(self) -> None:
        """Initialize."""
        pass

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle encoding change."""
        if event.control.id == "token-encoding":
            val = str(event.value)
            self.manager = TokenLabManager(model=val)
            if self.manager.encoding is None:
                self.notify(f"Error loading encoding: {self.manager.error}", severity="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-count":
            text = self.query_one("#token-input-text", TextArea).text
            if not text:
                self.notify("Please enter text to encode.", severity="error")
                return

            result = self.manager.count_tokens(text)
            if result["success"]:
                self.query_one("#token-count-label", Label).update(f"Tokens: {result['count']}")
                self.query_one("#token-input-tokens", TextArea).text = ", ".join(map(str, result["tokens"]))
                self.query_one("#token-output", TextArea).text = f"Successfully encoded to {result['count']} tokens."
                self.notify("Token count complete.", severity="information")
            else:
                self.notify(result["error"], severity="error")

        elif event.button.id == "btn-decode":
            tokens_str = self.query_one("#token-input-tokens", TextArea).text
            if not tokens_str:
                self.notify("Please enter tokens to decode.", severity="error")
                return

            try:
                tokens = [int(t.strip()) for t in tokens_str.split(",") if t.strip()]
            except ValueError:
                self.notify("Tokens must be a comma-separated list of integers.", severity="error")
                return

            result = self.manager.decode(tokens)
            if result["success"]:
                self.query_one("#token-output", TextArea).text = result["text"]
                self.notify("Decoding complete.", severity="information")
            else:
                self.notify(result["error"], severity="error")
