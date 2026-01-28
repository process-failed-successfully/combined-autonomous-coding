from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Label, Input, Button, DataTable, Markdown
from textual import on
from pathlib import Path
from datetime import datetime
from shared.cron_lab import CronLabManager

class CronLabTab(Container):
    """Tab for Cron Expression Lab."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Cron Expression Lab[/bold]", classes="welcome-text")

            with Container(classes="stat-box"):
                yield Label("Enter Cron Expression:")
                with Horizontal():
                    # Default to every 5 minutes
                    yield Input(placeholder="* * * * *", value="*/5 * * * *", id="cron-input")
                    yield Button("Analyze", id="btn-cron-analyze", variant="primary")

            with Container(classes="stat-box"):
                yield Label("[bold]Human Readable Description[/bold]")
                yield Label("", id="cron-desc-lbl")

            with Container(classes="stat-box"):
                yield Label("[bold]Next Occurrences[/bold]")
                yield DataTable(id="cron-table")

            with VerticalScroll(classes="stat-box"):
                yield Label("[bold]Cheatsheet[/bold]")
                yield Markdown("""
- `* * * * *` = Minute Hour Day(Month) Month Day(Week)
- `*/5 * * * *` = Every 5 minutes
- `0 0 * * *` = Every day at midnight
- `0 0 * * 0` = Every Sunday at midnight
- `0 9-17 * * 1-5` = Every hour from 9am to 5pm, Mon-Fri
                """)

    def on_mount(self) -> None:
        table = self.query_one("#cron-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Timestamp", "Relative")
        self.run_analysis()

    @on(Button.Pressed, "#btn-cron-analyze")
    def on_analyze(self) -> None:
        self.run_analysis()

    @on(Input.Submitted, "#cron-input")
    def on_submit(self) -> None:
        self.run_analysis()

    def run_analysis(self) -> None:
        expression = self.query_one("#cron-input", Input).value
        desc_lbl = self.query_one("#cron-desc-lbl", Label)
        table = self.query_one("#cron-table", DataTable)
        table.clear()

        if not expression:
            desc_lbl.update("Please enter an expression.")
            return

        # Description
        desc = CronLabManager.describe(expression)
        if desc == "Invalid expression" or desc.startswith("Invalid"):
             desc_lbl.update(f"[red]{desc}[/red]")
             # Still try to calc if possible? No, croniter will fail.
             return
        else:
             desc_lbl.update(f"[green]{desc}[/green]")

        # Next Runs
        try:
            runs = CronLabManager.get_next_runs(expression, count=10)
            now = datetime.now()
            for run in runs:
                delta = run - now

                # Format delta
                if delta.days > 0:
                    rel = f"in {delta.days}d {delta.seconds//3600}h"
                elif delta.seconds > 3600:
                    rel = f"in {delta.seconds//3600}h {(delta.seconds%3600)//60}m"
                elif delta.seconds > 60:
                    rel = f"in {delta.seconds//60}m {delta.seconds%60}s"
                else:
                    rel = f"in {delta.seconds}s"

                table.add_row(str(run), rel)
        except Exception as e:
            # Only notify if it wasn't caught by validate (e.g. range errors)
            if "Invalid" not in str(e):
                self.notify(f"Error calculating runs: {e}", severity="error")
            else:
                desc_lbl.update(f"[red]{e}[/red]")
