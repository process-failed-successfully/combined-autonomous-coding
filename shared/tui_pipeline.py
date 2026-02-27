from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Label, Button, DataTable, RichLog, Input, Select, TextArea
from textual.containers import Container, Horizontal, Vertical
from textual import on
import json
import asyncio

from shared.pipeline_lab import PipelineLabManager

class PipelineLabTab(Container):
    """Tab for chaining data transformations."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = PipelineLabManager()
        self.pipeline_steps = [] # List of (op_name, arg)

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: Input and Builder
            with Vertical(id="pipe-builder-container", classes="stat-box"):
                yield Label("[bold]Input Data[/bold]")
                yield TextArea(id="pipe-input")

                yield Label("[bold]Pipeline Steps[/bold]")

                with Horizontal():
                    ops = sorted(self.manager.operations.keys())
                    yield Select.from_values(ops, id="pipe-op-select", prompt="Select Operation")
                    yield Input(placeholder="Argument (optional)", id="pipe-arg-input")
                    yield Button("Add Step", id="btn-pipe-add", variant="primary")

                yield DataTable(id="pipe-steps-table")

                with Horizontal():
                    yield Button("Remove Selected", id="btn-pipe-remove", variant="error", disabled=True)
                    yield Button("Clear All", id="btn-pipe-clear", variant="default")
                    yield Button("Run Pipeline", id="btn-pipe-run", variant="success")

            # Right Pane: Output
            with Vertical(id="pipe-output-container", classes="stat-box"):
                yield Label("[bold]Output Result[/bold]")
                yield RichLog(id="pipe-output", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        table = self.query_one("#pipe-steps-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Order", "Operation", "Argument")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-pipe-add":
            self.add_step()
        elif event.button.id == "btn-pipe-remove":
            self.remove_step()
        elif event.button.id == "btn-pipe-clear":
            self.clear_pipeline()
        elif event.button.id == "btn-pipe-run":
            await self.run_pipeline()

    def add_step(self) -> None:
        select = self.query_one("#pipe-op-select", Select)
        arg_input = self.query_one("#pipe-arg-input", Input)

        op = select.value
        # DEBUG PRINT
        print(f"DEBUG: add_step triggered. Op: {op!r}")

        if not op or op == Select.BLANK:
            self.notify("Please select an operation.", severity="error")
            return

        arg = arg_input.value

        self.pipeline_steps.append((op, arg))
        self.refresh_table()

        # Clear inputs for convenience? Maybe keep op selected.
        arg_input.value = ""

    def remove_step(self) -> None:
        table = self.query_one("#pipe-steps-table", DataTable)
        if table.cursor_row is not None:
            index = table.cursor_row
            if 0 <= index < len(self.pipeline_steps):
                self.pipeline_steps.pop(index)
                self.refresh_table()
                self.query_one("#btn-pipe-remove").disabled = True

    def clear_pipeline(self) -> None:
        self.pipeline_steps = []
        self.refresh_table()

    def refresh_table(self) -> None:
        table = self.query_one("#pipe-steps-table", DataTable)
        table.clear()
        for i, (op, arg) in enumerate(self.pipeline_steps):
            table.add_row(str(i+1), op, arg or "")

    @on(DataTable.RowSelected, "#pipe-steps-table")
    def on_step_selected(self) -> None:
        self.query_one("#btn-pipe-remove").disabled = False

    async def run_pipeline(self) -> None:
        input_text = self.query_one("#pipe-input", TextArea).text
        output_log = self.query_one("#pipe-output", RichLog)

        output_log.clear()

        if not input_text:
            output_log.write("[yellow]Warning: Input is empty.[/yellow]")

        ops_strings = []
        for op, arg in self.pipeline_steps:
            if arg:
                ops_strings.append(f"{op} {arg}")
            else:
                ops_strings.append(op)

        output_log.write(f"[bold]Running Pipeline:[/bold] { ' -> '.join(ops_strings) }")

        try:
            result = await asyncio.to_thread(self.manager.process, input_text, ops_strings)

            output_log.write("\n[bold green]Result:[/bold green]")
            if isinstance(result, (dict, list)):
                output_log.write(json.dumps(result, indent=2))
            else:
                output_log.write(str(result))

        except Exception as e:
            output_log.write(f"\n[bold red]Error:[/bold red] {e}")
            self.notify(f"Pipeline failed: {e}", severity="error")
