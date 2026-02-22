from pathlib import Path
import tempfile
import os
import asyncio
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, Button, Input, TextArea, Select, RichLog
from textual import on
from shared.chart_lab import ChartLabManager

class ChartLabTab(Container):
    """Tab for visualizing data with ASCII charts."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        # Default chart size
        self.manager = ChartLabManager(width=100, height=25)
        self.current_data = []

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: Input
            with Vertical(id="chart-input-pane", classes="stat-box"):
                yield Label("[bold]Data Input[/bold]")
                yield Label("Paste CSV/JSON or load from file:")
                yield Input(placeholder="File path (e.g. data.csv)...", id="chart-file-input")
                yield Button("Load from File", id="btn-chart-load-file", variant="primary")
                yield TextArea(id="chart-text-input", language="json")
                yield Button("Load from Text", id="btn-chart-load-text", variant="warning")

            # Right Pane: Controls & Output
            with Vertical(id="chart-output-pane"):
                yield Label("[bold]Chart Configuration[/bold]")

                with Horizontal(classes="stat-box"):
                    yield Select([], id="select-chart-x", prompt="X Column")
                    yield Select([], id="select-chart-y", prompt="Y Column")
                    yield Select.from_values(["bar", "scatter", "line"], id="select-chart-type", value="bar")
                    yield Button("Plot", id="btn-chart-plot", variant="success", disabled=True)

                yield Label("[bold]Chart Output[/bold]")
                yield RichLog(id="chart-output-log", wrap=False, highlight=False, markup=False)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-chart-load-file":
            await self.load_from_file()
        elif event.button.id == "btn-chart-load-text":
            self.load_from_text()
        elif event.button.id == "btn-chart-plot":
            self.plot_chart()

    async def load_from_file(self) -> None:
        path_str = self.query_one("#chart-file-input", Input).value
        if not path_str:
            self.notify("Please enter a file path.", severity="error")
            return

        path = Path(path_str)
        if not path.exists():
            self.notify(f"File not found: {path}", severity="error")
            return

        try:
            # Run IO in thread
            self.current_data = await asyncio.to_thread(self.manager.load_data, path)
            self.notify(f"Loaded {len(self.current_data)} rows.")
            self.update_columns()
        except Exception as e:
            self.notify(f"Error loading file: {e}", severity="error")

    def load_from_text(self) -> None:
        content = self.query_one("#chart-text-input", TextArea).text
        if not content.strip():
            self.notify("Input is empty.", severity="warning")
            return

        # Write to temp file to reuse manager's load_data logic
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8') as tmp:
                tmp.write(content)
                tmp_path = tmp.name

            self.current_data = self.manager.load_data(tmp_path)
            self.notify(f"Loaded {len(self.current_data)} rows from text.")
            self.update_columns()

        except Exception as e:
            self.notify(f"Error parsing text: {e}", severity="error")
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def update_columns(self) -> None:
        if not self.current_data:
            return

        # Infer columns from first row
        row = self.current_data[0]
        columns = list(row.keys())

        # Update selects
        select_x = self.query_one("#select-chart-x", Select)
        select_y = self.query_one("#select-chart-y", Select)

        options = [(c, c) for c in columns]
        select_x.set_options(options)
        select_y.set_options(options)

        # Select first two if available
        if len(columns) > 0:
            select_x.value = columns[0]
        if len(columns) > 1:
            select_y.value = columns[1]

        self.query_one("#btn-chart-plot").disabled = False

    def plot_chart(self) -> None:
        if not self.current_data:
            return

        x_col = self.query_one("#select-chart-x", Select).value
        y_col = self.query_one("#select-chart-y", Select).value
        chart_type = self.query_one("#select-chart-type", Select).value

        if not x_col or not y_col:
            self.notify("Please select X and Y columns.", severity="error")
            return

        log = self.query_one("#chart-output-log", RichLog)
        log.clear()

        try:
            output = ""
            if chart_type == "bar":
                output = self.manager.plot_bar(self.current_data, x_col, y_col)
            elif chart_type == "scatter":
                output = self.manager.plot_scatter(self.current_data, x_col, y_col)
            elif chart_type == "line":
                output = self.manager.plot_line(self.current_data, x_col, y_col)

            log.write(output)
        except Exception as e:
            self.notify(f"Plot error: {e}", severity="error")
            log.write(f"Error: {e}")
