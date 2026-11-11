from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Input, Label, Markdown
from textual.widgets import TabPane

from shared.chmod_lab import ChmodLabManager

class ChmodLabTab(TabPane):
    """Tab for Chmod Lab."""

    DEFAULT_CSS = """
    ChmodLabTab {
        layout: vertical;
        height: 100%;
    }

    .chmod-box {
        height: auto;
        border: solid $accent;
        padding: 1;
        margin: 1;
    }

    #chmod-output {
        height: 1fr;
    }
    """

    def __init__(self, *args, **kwargs):
        super().__init__("Chmod Lab", id="tab-chmod-lab", **kwargs)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Chmod Lab[/bold]", classes="welcome-text")

            # Input Section
            with Vertical(classes="chmod-box"):
                yield Label("Permission (e.g., '755' or 'rwxr-xr-x'):")
                yield Input(id="chmod-input", placeholder="Enter permission...")

            # Controls Section
            with Horizontal(classes="chmod-box"):
                yield Button("Analyze", id="btn-chmod-analyze", variant="primary")

            # Output Section
            with Vertical(classes="chmod-box"):
                yield Markdown(id="chmod-output")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-chmod-analyze":
            self.analyze_permission()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "chmod-input":
            self.analyze_permission()

    def analyze_permission(self) -> None:
        input_widget = self.query_one("#chmod-input", Input)
        output_widget = self.query_one("#chmod-output", Markdown)

        perm = input_widget.value.strip()
        if not perm:
            output_widget.update("Error: Input cannot be empty.")
            return

        try:
            res = ChmodLabManager.parse(perm)
            md = f"""
### Results
**Octal:** `{res['octal']}`
**Symbolic:** `{res['symbolic']}`
**Binary:** `{res['binary']}`

- **Owner:** {res['owner']}
- **Group:** {res['group']}
- **Public:** {res['public']}
            """
            output_widget.update(md)
        except Exception as e:
            output_widget.update(f"**Error:** {str(e)}")
