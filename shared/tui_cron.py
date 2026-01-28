from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Input, Label, RichLog, Button
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual import on
from shared.cron_lab import CronLabManager

class CronLabTab(Container):
    """Tab for experimenting with Cron expressions."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = CronLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Cron Lab[/bold]", classes="welcome-text")

            # Input Section
            with Container(classes="stat-box"):
                yield Label("Cron Expression:")
                with Horizontal():
                    yield Input(placeholder="e.g. */5 * * * *", id="cron-input")
                    yield Button("Analyze", id="btn-cron-analyze", variant="primary")

            # Status
            with Container(classes="stat-box"):
                yield Label("Status: ", id="lbl-cron-status")
                yield Label("Description: ", id="lbl-cron-desc")

            # Output
            with VerticalScroll(classes="stat-box", id="cron-output-container"):
                yield Label("[bold]Next Occurrences[/bold]")
                yield RichLog(id="cron-output", wrap=True, highlight=False, markup=True)

    @on(Input.Changed, "#cron-input")
    def on_input_changed(self, event: Input.Changed) -> None:
        self.analyze_cron(event.value)

    @on(Button.Pressed, "#btn-cron-analyze")
    def on_analyze(self) -> None:
        val = self.query_one("#cron-input", Input).value
        self.analyze_cron(val)

    def analyze_cron(self, expression: str) -> None:
        status_lbl = self.query_one("#lbl-cron-status", Label)
        desc_lbl = self.query_one("#lbl-cron-desc", Label)
        output = self.query_one("#cron-output", RichLog)

        output.clear()

        if not expression:
            status_lbl.update("Status: Waiting for input")
            desc_lbl.update("Description: ")
            return

        is_valid = self.manager.validate(expression)

        if is_valid:
            status_lbl.update("Status: [bold green]Valid[/bold green]")
            desc = self.manager.describe(expression)
            desc_lbl.update(f"Description: {desc}")

            next_runs = self.manager.get_next_occurrences(expression, count=10)
            for dt in next_runs:
                output.write(dt.strftime("%Y-%m-%d %H:%M:%S"))
        else:
            status_lbl.update("Status: [bold red]Invalid[/bold red]")
            desc_lbl.update("Description: Invalid format")
            output.write("[red]Invalid cron expression.[/red]")
