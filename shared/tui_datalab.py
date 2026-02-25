from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, DataTable, Button, DirectoryTree, RichLog, Input
from textual import on
from shared.datalab import DataLabManager
from shared.charts import draw_ascii_bar_chart

class DataLabTab(Container):
    def __init__(self, project_dir: Path, **kwargs):
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = DataLabManager(project_dir)
        self.current_data = []

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical(id="datalab-left-pane", classes="stat-box"):
                yield Label("[bold]Data Files[/bold]")
                # We start from project root
                yield DirectoryTree(str(self.project_dir), id="datalab-tree")

            with Vertical(id="datalab-main-pane"):
                yield Label("[bold]Data Preview[/bold]")
                yield DataTable(id="datalab-table")

                with Horizontal(classes="stat-box"):
                    yield Input(placeholder="Column name...", id="datalab-col-input")
                    yield Button("Analyze Column", id="btn-datalab-analyze", variant="primary")

                yield RichLog(id="datalab-stats-log", markup=True, wrap=True)

    def on_mount(self) -> None:
        table = self.query_one("#datalab-table", DataTable)
        table.cursor_type = "row"

    @on(DirectoryTree.FileSelected, "#datalab-tree")
    def on_file_selected(self, event: DirectoryTree.FileSelected):
        path = event.path
        if path.suffix in [".csv", ".json", ".xlsx"]:
            self.load_data(path)
        else:
            self.notify("Unsupported file type. Select .csv, .json, or .xlsx", severity="warning")

    def load_data(self, path: Path):
        self.current_data = self.manager.load_file(path)
        table = self.query_one("#datalab-table", DataTable)
        table.clear(columns=True)

        if not self.current_data:
            self.notify("No data found or invalid format.", severity="warning")
            return

        # Infer columns
        columns = list(self.current_data[0].keys())
        table.add_columns(*columns)

        # Add first 100 rows
        for row in self.current_data[:100]:
            # Convert all values to string for display
            row_data = [str(row.get(col, "")) for col in columns]
            table.add_row(*row_data)

        self.notify(f"Loaded {len(self.current_data)} rows from {path.name}.")

    @on(Button.Pressed, "#btn-datalab-analyze")
    def analyze_column(self):
        col_name = self.query_one("#datalab-col-input", Input).value
        if not col_name:
            self.notify("Please enter a column name.", severity="error")
            return

        stats = self.manager.get_statistics(self.current_data)
        log = self.query_one("#datalab-stats-log", RichLog)
        log.clear()

        if col_name in stats:
            s = stats[col_name]
            log.write(f"[bold]{col_name} Statistics[/bold]")
            log.write(f"Count: {s['count']}")
            log.write(f"Min: {s['min']}")
            log.write(f"Max: {s['max']}")
            log.write(f"Mean: {s['mean']:.2f}")

            # Simple Chart: If we have numeric data, we can try to bin it?
            # Or just show a simple visualization of min/mean/max?
            # Let's create a simple dict for chart
            chart_data = {
                "Min": s['min'],
                "Mean": s['mean'],
                "Max": s['max']
            }
            chart = draw_ascii_bar_chart(chart_data, f"{col_name} Distribution")
            log.write("\n" + chart)

        else:
            log.write(f"[red]Column '{col_name}' not numeric or found.[/red]")
            # List available numeric columns
            if stats:
                log.write(f"Available numeric columns: {', '.join(stats.keys())}")
