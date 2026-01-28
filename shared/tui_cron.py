from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Label, Input, RichLog, Button
from textual import on
from shared.cron_lab import CronLabManager

class CronLabTab(Container):
    """Tab for experimenting with cron expressions."""

    def __init__(self, project_dir=None, **kwargs):
        super().__init__(**kwargs)
        self.manager = CronLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Cron Lab[/bold]", classes="welcome-text")

            with Vertical(classes="stat-box"):
                yield Label("Cron Expression:")
                yield Input(placeholder="* * * * *", id="cron-input")
                yield Button("Analyze", id="btn-cron-analyze", variant="primary")

            with Vertical(classes="stat-box"):
                yield Label("[bold]Explanation[/bold]")
                yield Label("", id="cron-explanation")

            with Vertical(classes="stat-box"):
                yield Label("[bold]Next Occurrences[/bold]")
                yield RichLog(id="cron-next-runs", wrap=True, highlight=True, markup=True)

    @on(Button.Pressed, "#btn-cron-analyze")
    def on_analyze(self) -> None:
        self.analyze_expression()

    @on(Input.Submitted, "#cron-input")
    def on_submit(self) -> None:
        self.analyze_expression()

    def analyze_expression(self) -> None:
        expr = self.query_one("#cron-input", Input).value
        explanation_lbl = self.query_one("#cron-explanation", Label)
        next_runs_log = self.query_one("#cron-next-runs", RichLog)

        next_runs_log.clear()

        if not expr:
            explanation_lbl.update("[yellow]Please enter an expression.[/yellow]")
            return

        if not self.manager.validate(expr):
            explanation_lbl.update("[red]Invalid cron expression.[/red]")
            return

        # Explain
        explanation = self.manager.explain(expr)
        explanation_lbl.update(f"[green]{explanation}[/green]")

        # Next runs
        try:
            next_runs = self.manager.next_occurrences(expr, count=10)
            for run in next_runs:
                next_runs_log.write(f"- {run}")
        except Exception as e:
            next_runs_log.write(f"[red]Error calculating next runs: {e}[/red]")
