from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, TextArea, Input
from textual.widgets import TabPane
from shared.pipeline_lab import PipelineLabManager
import json

class PipelineLabTab(TabPane):
    """Tab for Pipeline Lab (Chaining transformations)."""

    def __init__(self, **kwargs):
        super().__init__("Pipeline Lab", id="tab-pipeline", **kwargs)

    DEFAULT_CSS = """
    PipelineLabTab {
        layout: vertical;
        height: 100%;
    }

    .pipeline-box {
        height: auto;
        border: solid $accent;
        padding: 1;
        margin: 1;
    }

    #pipeline-input {
        height: 1fr;
    }

    #pipeline-output {
        height: 1fr;
    }

    #pipeline-ops {
        width: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Pipeline Lab (Data Transformations)[/bold]", classes="welcome-text")

            with Vertical(classes="pipeline-box"):
                yield Label("Input Data:")
                yield TextArea(id="pipeline-input", show_line_numbers=False)

            with Horizontal(classes="pipeline-box"):
                yield Label("Operations (separate with '|'): ", classes="label-inline")
                yield Input(id="pipeline-ops", placeholder="e.g. json-parse | json-get items | count")
                yield Button("Process", id="btn-pipeline-process", variant="primary")
                yield Button("Clear", id="btn-pipeline-clear", variant="error")

            with Vertical(classes="pipeline-box"):
                yield Label("Output Data:")
                yield TextArea(id="pipeline-output", read_only=True, show_line_numbers=False)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-pipeline-process":
            self.process_pipeline()
        elif event.button.id == "btn-pipeline-clear":
            self.clear_content()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "pipeline-ops":
            self.process_pipeline()

    def process_pipeline(self) -> None:
        input_data = self.query_one("#pipeline-input", TextArea).text
        ops_text = self.query_one("#pipeline-ops", Input).value
        output_area = self.query_one("#pipeline-output", TextArea)

        if not input_data:
            self.notify("Input is empty.", severity="warning")
            return

        ops = [op.strip() for op in ops_text.split("|") if op.strip()]
        if not ops:
            self.notify("No operations specified.", severity="warning")
            return

        manager = PipelineLabManager()
        try:
            result = manager.process(input_data, ops)
            if isinstance(result, (dict, list)):
                output_area.text = json.dumps(result, indent=2)
            else:
                output_area.text = str(result)
            self.notify("Pipeline executed successfully.", severity="information")
        except Exception as e:
            output_area.text = f"Error: {e}"
            self.notify(f"Pipeline Error: {e}", severity="error")

    def clear_content(self) -> None:
        self.query_one("#pipeline-input", TextArea).text = ""
        self.query_one("#pipeline-ops", Input).value = ""
        self.query_one("#pipeline-output", TextArea).text = ""
        self.notify("Cleared.")
