import json
from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, TextArea
from shared.csp_lab import CspLabManager

class CspLabTab(Container):
    """Tab for CSP Lab."""

    DEFAULT_CSS = """
    CspLabTab {
        layout: vertical;
        height: 100%;
    }
    .csp-box {
        height: auto;
        border: solid $accent;
        padding: 1;
        margin: 1;
    }
    #csp-input, #csp-output {
        height: 1fr;
    }
    """

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = CspLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Content Security Policy (CSP) Lab[/bold]", classes="welcome-text")

            # Input Section
            with Vertical(classes="csp-box"):
                yield Label("Input CSP String:")
                yield TextArea(id="csp-input", show_line_numbers=False)

            # Controls Section
            with Horizontal(classes="csp-box"):
                yield Button("Parse", id="btn-csp-parse", variant="primary")
                yield Button("Validate", id="btn-csp-validate", variant="warning")
                yield Button("Clear", id="btn-csp-clear", variant="error")

            # Output Section
            with Vertical(classes="csp-box"):
                yield Label("Output:")
                yield TextArea(id="csp-output", read_only=True, show_line_numbers=False)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-csp-parse":
            self.parse_csp()
        elif event.button.id == "btn-csp-validate":
            self.validate_csp()
        elif event.button.id == "btn-csp-clear":
            self.clear_content()

    def parse_csp(self) -> None:
        text = self.query_one("#csp-input", TextArea).text.strip()
        output_area = self.query_one("#csp-output", TextArea)

        if not text:
            self.notify("Input is empty.", severity="warning")
            return

        try:
            parsed = self.manager.parse(text)
            output_area.text = json.dumps(parsed, indent=2)
            self.notify("Parsed successfully.")
        except Exception as e:
            output_area.text = f"Error: {e}"
            self.notify(f"Exception: {e}", severity="error")

    def validate_csp(self) -> None:
        text = self.query_one("#csp-input", TextArea).text.strip()
        output_area = self.query_one("#csp-output", TextArea)

        if not text:
            self.notify("Input is empty.", severity="warning")
            return

        try:
            is_valid, warnings = self.manager.validate(text)
            if is_valid:
                output_area.text = "✅ Policy is valid (no warnings)."
            else:
                out = "❌ Policy has warnings:\n\n"
                for w in warnings:
                    out += f"  - {w}\n"
                output_area.text = out
            self.notify("Validation complete.")
        except Exception as e:
            output_area.text = f"Error: {e}"
            self.notify(f"Exception: {e}", severity="error")

    def clear_content(self) -> None:
        self.query_one("#csp-input", TextArea).text = ""
        self.query_one("#csp-output", TextArea).text = ""
        self.notify("Cleared.")
