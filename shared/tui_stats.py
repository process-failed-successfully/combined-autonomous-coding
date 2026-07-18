from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Label, DataTable, Button, RichLog, Input
from textual import on
from shared.stats_lab import CodeStatsManager
from shared.charts import draw_ascii_bar_chart

class StatsTab(Container):
    """Tab for visualizing codebase statistics."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = CodeStatsManager(project_dir)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Codebase Statistics[/bold]", classes="welcome-text")

            # Chart Area
            with Vertical(classes="stat-box"):
                yield Label("[bold]Distribution (LOC)[/bold]")
                yield RichLog(id="stats-chart-log", wrap=False, highlight=False)

            # Table Area
            with Vertical(classes="stat-box", id="stats-table-container"):
                yield Label("[bold]Detailed Breakdown[/bold]")
                yield Input(placeholder="Exclude dirs (comma-separated, e.g. tests,node_modules)", id="stats-exclude-input")
                yield DataTable(id="stats-table")

            yield Button("Refresh", id="btn-stats-refresh", variant="primary")

    def on_mount(self) -> None:
        table = self.query_one("#stats-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Language", "Files", "Lines", "Code", "Comments", "Blanks")
        self.refresh_stats()

    @on(Button.Pressed, "#btn-stats-refresh")
    def on_refresh(self) -> None:
        self.refresh_stats()
        self.notify("Statistics refreshed.")

    def refresh_stats(self) -> None:
        self.notify("Scanning codebase...")

        exclude_val = self.query_one("#stats-exclude-input", Input).value.strip()
        excludes = [x.strip() for x in exclude_val.split(",")] if exclude_val else []
        self.manager = CodeStatsManager(self.project_dir, exclude=excludes)

        # Run in thread to avoid blocking UI
        import asyncio
        asyncio.create_task(self._async_scan())

    async def _async_scan(self) -> None:
        import asyncio

        stats = await asyncio.to_thread(self.manager.scan)
        self._update_ui(stats)

    def _update_ui(self, stats: dict) -> None:
        # Update Table
        table = self.query_one("#stats-table", DataTable)
        table.clear()

        totals = {"files": 0, "lines": 0, "code": 0, "comment": 0, "blank": 0}

        # Sort by code lines desc
        sorted_stats = dict(sorted(stats.items(), key=lambda item: item[1]["code"], reverse=True))

        for lang, info in sorted_stats.items():
            table.add_row(
                lang,
                str(info["files"]),
                str(info["lines"]),
                str(info["code"]),
                str(info["comment"]),
                str(info["blank"])
            )
            for k in totals:
                totals[k] += info[k]

        try:
            table.add_section()
        except AttributeError:
            # Fallback for Textual < 0.81.0 where add_section doesn't exist
            # We'll just add a visual separator row instead
            table.add_row("---", "---", "---", "---", "---", "---")

        table.add_row(
            "[bold]TOTAL[/bold]",
            str(totals["files"]),
            str(totals["lines"]),
            str(totals["code"]),
            str(totals["comment"]),
            str(totals["blank"]),
        )

        # Update Chart
        chart_log = self.query_one("#stats-chart-log", RichLog)
        chart_log.clear()

        chart_data = {lang: info["code"] for lang, info in sorted_stats.items()}
        chart = draw_ascii_bar_chart(chart_data, "Lines of Code by Language", width=60)
        chart_log.write(chart)
