import sys
from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, TextArea, Button, Select, Checkbox, Static
from textual import on

from shared.set_lab import SetLabManager

class SetLabTab(Container):
    """Tab for Set Operations (union, intersect, difference, etc)."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = SetLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Set Operations Lab[/bold]", classes="welcome-text")

            # Inputs
            with Horizontal():
                with Vertical(classes="stat-box", id="set-a-pane"):
                    yield Label("List A (One per line)")
                    yield TextArea(id="set-a-input")

                with Vertical(classes="stat-box", id="set-b-pane"):
                    yield Label("List B (One per line)")
                    yield TextArea(id="set-b-input")

            # Controls
            with Horizontal(classes="stat-box"):
                yield Label("Operation:")
                yield Select.from_values(
                    ["union", "intersect", "difference", "sym_diff", "is_subset", "is_superset"],
                    id="set-operation",
                    value="intersect"
                )
                yield Checkbox("Ignore Case", id="set-chk-case")
                yield Checkbox("Trim Whitespace", id="set-chk-trim", value=True)
                yield Button("Compute", id="btn-set-compute", variant="primary")

            # Result
            with Vertical(classes="stat-box"):
                with Horizontal():
                    yield Label("[bold]Result[/bold]")
                    yield Label("", id="set-result-count", classes="dim")
                yield TextArea(id="set-result-output", read_only=True)

    @on(Button.Pressed, "#btn-set-compute")
    def on_compute(self) -> None:
        text_a = self.query_one("#set-a-input", TextArea).text
        text_b = self.query_one("#set-b-input", TextArea).text

        list_a = [s for s in text_a.splitlines() if s]
        list_b = [s for s in text_b.splitlines() if s]

        operation = self.query_one("#set-operation", Select).value
        if not operation:
            self.notify("Please select an operation.", severity="error")
            return

        ignore_case = self.query_one("#set-chk-case", Checkbox).value
        trim = self.query_one("#set-chk-trim", Checkbox).value

        try:
            result = self.manager.perform_operation(list_a, list_b, operation, ignore_case, trim)

            output_area = self.query_one("#set-result-output", TextArea)
            count_label = self.query_one("#set-result-count", Label)

            if isinstance(result, bool):
                output_area.text = str(result)
                count_label.update("")
            else:
                output_area.text = "\n".join(result)
                count_label.update(f"({len(result)} items)")

            self.notify("Set operation complete.")
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")
