from pathlib import Path
from typing import List, Dict, Any, Optional

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Label, Input, TextArea, Button, DataTable, Select, RichLog, Static
from textual import on

from shared.datalab import DataLabManager
from shared.charts import draw_ascii_bar_chart, draw_ascii_line_chart, draw_ascii_scatter_chart

class DataLabTab(Container):
    """Tab for Data Analysis and Visualization."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = DataLabManager(project_dir)
        self.loaded_data: List[Dict[str, Any]] = []
        self.columns: List[str] = []

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: Data Source
            with Vertical(id="datalab-source-pane", classes="stat-box"):
                yield Label("[bold]Data Source[/bold]")
                yield Label("File Path:")
                yield Input(placeholder="Path to CSV/JSON...", id="datalab-path")
                yield Label("Or Paste Data:")
                yield TextArea(id="datalab-paste", language="json")
                yield Button("Load Data", id="btn-datalab-load", variant="primary")

            # Center Pane: Preview
            with Vertical(id="datalab-preview-pane"):
                yield Label("[bold]Data Preview (Top 50)[/bold]")
                yield DataTable(id="datalab-table")

            # Right Pane: Analysis & Viz
            with Vertical(id="datalab-viz-pane", classes="stat-box"):
                with VerticalScroll():
                    yield Label("[bold]Analysis[/bold]")
                    yield Select([], id="datalab-stats-col", prompt="Select Column to Analyze")
                    yield RichLog(id="datalab-stats-log", height=8, wrap=True, markup=True)

                    yield Label("[bold]Visualization[/bold]")
                    yield Select([], id="datalab-x-col", prompt="X Axis")
                    yield Select([], id="datalab-y-col", prompt="Y Axis")
                    yield Select.from_values(["Bar", "Line", "Scatter"], id="datalab-chart-type", value="Bar")
                    yield Button("Generate Chart", id="btn-datalab-chart", variant="success")

                    yield RichLog(id="datalab-chart-view", markup=True)

    def on_mount(self) -> None:
        table = self.query_one("#datalab-table", DataTable)
        table.cursor_type = "row"

    @on(Button.Pressed, "#btn-datalab-load")
    def on_load_data(self) -> None:
        path = self.query_one("#datalab-path", Input).value
        paste = self.query_one("#datalab-paste", TextArea).text

        source = path if path else paste
        if not source:
            self.notify("Please provide a file path or paste data.", severity="error")
            return

        self.notify("Loading data...", severity="information")

        try:
            self.loaded_data = self.manager.load_data(source)
            if not self.loaded_data:
                self.notify("No data found or parsed.", severity="warning")
                return

            self.notify(f"Loaded {len(self.loaded_data)} records.")
            self.refresh_preview()
            self.refresh_columns()

        except Exception as e:
            self.notify(f"Error loading data: {e}", severity="error")

    def refresh_preview(self) -> None:
        table = self.query_one("#datalab-table", DataTable)
        table.clear(columns=True)

        if not self.loaded_data:
            return

        # Infer columns
        self.columns = self.manager.get_columns(self.loaded_data)
        table.add_columns(*self.columns)

        # Add rows (limit to 50)
        rows = []
        for item in self.loaded_data[:50]:
            row = [str(item.get(col, "")) for col in self.columns]
            rows.append(row)

        table.add_rows(rows)

    def refresh_columns(self) -> None:
        options = [(c, c) for c in self.columns]

        # Update selects
        for select_id in ["#datalab-stats-col", "#datalab-x-col", "#datalab-y-col"]:
            select = self.query_one(select_id, Select)
            select.set_options(options)

    @on(Select.Changed, "#datalab-stats-col")
    def on_stats_col_changed(self, event: Select.Changed) -> None:
        col = event.value
        if not col or not self.loaded_data:
            return

        log = self.query_one("#datalab-stats-log", RichLog)
        log.clear()

        try:
            stats = self.manager.analyze_column(self.loaded_data, col)
            if "error" in stats:
                log.write(f"[red]{stats['error']}[/red]")
            else:
                log.write(f"[bold]{col}[/bold] Statistics:")
                for k, v in stats.items():
                    if isinstance(v, float):
                        log.write(f"  {k.capitalize()}: {v:.4f}")
                    else:
                        log.write(f"  {k.capitalize()}: {v}")
        except Exception as e:
            log.write(f"Error: {e}")

    @on(Button.Pressed, "#btn-datalab-chart")
    def on_generate_chart(self) -> None:
        if not self.loaded_data:
            self.notify("No data loaded.", severity="warning")
            return

        x_col = self.query_one("#datalab-x-col", Select).value
        y_col = self.query_one("#datalab-y-col", Select).value
        chart_type = self.query_one("#datalab-chart-type", Select).value

        log = self.query_one("#datalab-chart-view", RichLog)
        log.clear()

        if not y_col:
            self.notify("Y Axis column is required.", severity="error")
            return

        # Prepare data
        try:
            chart_str = ""

            if chart_type == "Bar":
                # Aggregate or raw? Let's do simple raw mapping for now
                # Or if X is categorical, aggregate Y?
                # For simplicity: x labels, y values.

                # Limit to 20 items for bar chart to fit
                limit = 20
                data_slice = self.loaded_data[:limit]

                chart_data = {}
                for row in data_slice:
                    label = str(row.get(x_col, "Index")) if x_col else f"Row {data_slice.index(row)}"
                    val = row.get(y_col, 0)
                    if isinstance(val, (int, float)):
                        chart_data[label] = float(val)

                chart_str = draw_ascii_bar_chart(chart_data, title=f"{y_col} by {x_col or 'Index'}", color="blue")

            elif chart_type == "Line":
                # Just Y values
                data_slice = self.loaded_data[:60] # Limit for width
                values = []
                labels = []
                for row in data_slice:
                    val = row.get(y_col, 0)
                    if isinstance(val, (int, float)):
                        values.append(float(val))
                        if x_col:
                            labels.append(str(row.get(x_col, "")))

                chart_str = draw_ascii_line_chart(values, labels=labels, color="green")

            elif chart_type == "Scatter":
                if not x_col:
                    self.notify("X Axis required for Scatter plot.", severity="error")
                    return

                points = []
                for row in self.loaded_data:
                    x = row.get(x_col)
                    y = row.get(y_col)
                    if isinstance(x, (int, float)) and isinstance(y, (int, float)):
                        points.append((float(x), float(y)))

                chart_str = draw_ascii_scatter_chart(points, color="yellow")

            log.write(chart_str)

        except Exception as e:
            log.write(f"[red]Error generating chart: {e}[/red]")
            self.notify(f"Chart error: {e}", severity="error")
