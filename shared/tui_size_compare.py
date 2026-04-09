from textual.app import ComposeResult
from textual.widgets import Button, TextArea, Label, TabPane
from textual.containers import Vertical, Horizontal
from shared.size_compare_lab import SizeCompareManager

class SizeCompareTab(TabPane):
    """TUI Tab for comparing serialization sizes."""

    def __init__(self, project_dir, id: str = "tab-size-compare"):
        super().__init__("Size Compare", id=id)
        self.project_dir = project_dir
        self.manager = SizeCompareManager()

    def compose(self) -> ComposeResult:
        with Vertical(classes="stat-box"):
            yield Label("Input JSON:")
            yield TextArea(id="size-cmp-input", language="json", text='{\n  "key": "value"\n}')
            with Horizontal():
                yield Button("Compare Sizes", id="btn-size-compare", variant="primary")
            yield Label("Output (Sizes in bytes):")
            yield TextArea(id="size-cmp-output", read_only=True)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-size-compare":
            self.do_compare()

    def do_compare(self) -> None:
        text = self.query_one("#size-cmp-input", TextArea).text
        out = self.query_one("#size-cmp-output", TextArea)

        if not text.strip():
            # Handle notification gracefully if available
            try:
                self.app.notify("Input required.", severity="error")
            except Exception:
                pass
            return

        try:
            res = self.manager.compare_sizes(text)
            out.text = res
            try:
                self.app.notify("Comparison complete.")
            except Exception:
                pass
        except Exception as e:
            try:
                self.app.notify(f"Error: {e}", severity="error")
            except Exception:
                pass
            out.text = f"Error: {e}"
