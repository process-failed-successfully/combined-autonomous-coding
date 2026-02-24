from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, Button, ListView, ListItem, RichLog, TextArea, Input
from textual import on
from shared.pipeline_lab import PipelineLabManager
import json

class PipelineLabTab(Container):
    """Tab for interactive data pipeline construction."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = PipelineLabManager()
        self.pipeline_steps = []  # List of strings (e.g. "upper", "grep foo")

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: Operations Library
            with Vertical(id="pipe-ops-container", classes="stat-box"):
                yield Label("[bold]Operations[/bold]")
                yield ListView(id="pipe-ops-list")
                yield Input(placeholder="Filter operations...", id="pipe-ops-filter")

            # Center Pane: Pipeline Builder
            with Vertical(id="pipe-builder-container"):
                yield Label("[bold]Pipeline[/bold]")

                # Active Steps List
                yield ListView(id="pipe-steps-list")

                # Controls for selected step
                with Horizontal(classes="stat-box"):
                    yield Button("Add Selected Op", id="btn-pipe-add", variant="primary")
                    yield Button("Remove Step", id="btn-pipe-remove", variant="error")

                with Horizontal(classes="stat-box"):
                    yield Button("Move Up", id="btn-pipe-up", variant="default")
                    yield Button("Move Down", id="btn-pipe-down", variant="default")
                    yield Button("Clear All", id="btn-pipe-clear", variant="warning")

                # Parameter Input for the operation being added (or editing?)
                # For simplicity, we'll have an input for "Argument" that applies when Adding
                yield Label("Operation Argument (optional):")
                yield Input(placeholder="e.g. pattern for grep...", id="pipe-op-arg")

            # Right Pane: Input / Output
            with Vertical(id="pipe-io-container"):
                yield Label("[bold]Input Data[/bold]")
                yield TextArea("Hello World\nFoo Bar\n123", id="pipe-input", language="text")

                yield Label("[bold]Output Result[/bold]")
                yield RichLog(id="pipe-output", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        self.load_operations()
        self.update_output()

    def load_operations(self, filter_text: str = "") -> None:
        list_view = self.query_one("#pipe-ops-list", ListView)
        list_view.clear()

        ops = sorted(self.manager.operations.keys())
        for op in ops:
            if filter_text and filter_text.lower() not in op.lower():
                continue
            list_view.append(ListItem(Label(op)))

    @on(Input.Changed, "#pipe-ops-filter")
    def on_filter_changed(self, event: Input.Changed) -> None:
        self.load_operations(event.value)

    @on(Input.Changed, "#pipe-input")
    def on_input_changed(self, event: Input.Changed) -> None:
        self.update_output()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-pipe-add":
            self.add_step()
        elif event.button.id == "btn-pipe-remove":
            self.remove_step()
        elif event.button.id == "btn-pipe-up":
            self.move_step(-1)
        elif event.button.id == "btn-pipe-down":
            self.move_step(1)
        elif event.button.id == "btn-pipe-clear":
            self.clear_pipeline()

    def add_step(self) -> None:
        ops_list = self.query_one("#pipe-ops-list", ListView)
        if ops_list.index is None:
            return

        # Get selected op name
        item = ops_list.children[ops_list.index]
        op_name = str(item.query_one(Label).renderable)

        # Get arg
        arg = self.query_one("#pipe-op-arg", Input).value.strip()

        step = f"{op_name} {arg}" if arg else op_name
        self.pipeline_steps.append(step)

        self.refresh_steps_list()
        self.update_output()

        # Clear arg input for next use
        self.query_one("#pipe-op-arg").value = ""

    def remove_step(self) -> None:
        steps_list = self.query_one("#pipe-steps-list", ListView)
        if steps_list.index is not None:
            del self.pipeline_steps[steps_list.index]
            self.refresh_steps_list()
            self.update_output()

    def move_step(self, delta: int) -> None:
        steps_list = self.query_one("#pipe-steps-list", ListView)
        idx = steps_list.index

        if idx is None:
            return

        new_idx = idx + delta
        if 0 <= new_idx < len(self.pipeline_steps):
            self.pipeline_steps[idx], self.pipeline_steps[new_idx] = self.pipeline_steps[new_idx], self.pipeline_steps[idx]
            self.refresh_steps_list()
            # Reselect the item at new index
            steps_list.index = new_idx
            self.update_output()

    def clear_pipeline(self) -> None:
        self.pipeline_steps = []
        self.refresh_steps_list()
        self.update_output()

    def refresh_steps_list(self) -> None:
        list_view = self.query_one("#pipe-steps-list", ListView)
        list_view.clear()
        for i, step in enumerate(self.pipeline_steps):
            list_view.append(ListItem(Label(f"{i+1}. {step}")))

    def update_output(self) -> None:
        input_text = self.query_one("#pipe-input", TextArea).text
        output_log = self.query_one("#pipe-output", RichLog)
        output_log.clear()

        if not self.pipeline_steps:
            output_log.write(input_text)
            return

        try:
            result = self.manager.process(input_text, self.pipeline_steps)

            # Format output
            if isinstance(result, (dict, list)):
                output_log.write(json.dumps(result, indent=2))
            else:
                output_log.write(str(result))

        except Exception as e:
            output_log.write(f"[bold red]Error:[/bold red] {e}")
