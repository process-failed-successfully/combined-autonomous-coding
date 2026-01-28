from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, Button, DataTable, Input, Static
from textual import on
from pathlib import Path
from shared.cron_lab import CronLabManager

class CronLabTab(Container):
    """Tab for experimenting with Cron expressions."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = CronLabManager(project_dir)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Cron Lab[/bold]", classes="welcome-text")

            # Input Section
            with Container(classes="stat-box"):
                yield Label("Cron Expression:")
                with Horizontal():
                    yield Input(placeholder="* * * * *", id="cron-input")
                    yield Button("Analyze", id="btn-cron-analyze", variant="primary")
                yield Label("", id="cron-validation-lbl")

            # Explanation
            with Container(classes="stat-box"):
                yield Label("[bold]Explanation[/bold]")
                yield Static("Enter an expression to see explanation.", id="cron-explanation")

            # Next Runs
            with Container(classes="stat-box"):
                yield Label("[bold]Next 5 Runs[/bold]")
                yield DataTable(id="cron-runs-table")

            # Generator (Optional Helper)
            with Container(classes="stat-box"):
                yield Label("[bold]Generator (Experimental)[/bold]")
                with Horizontal():
                    yield Input(placeholder="e.g. 'every day at 2am'", id="cron-gen-input")
                    yield Button("Generate", id="btn-cron-gen", variant="warning")

    def on_mount(self) -> None:
        table = self.query_one("#cron-runs-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Run Time", "Relative")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cron-analyze":
            self.analyze_expression()
        elif event.button.id == "btn-cron-gen":
            self.generate_expression()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "cron-input":
            self.analyze_expression()
        elif event.input.id == "cron-gen-input":
            self.generate_expression()

    def analyze_expression(self) -> None:
        expression = self.query_one("#cron-input", Input).value.strip()
        if not expression:
            return

        valid_lbl = self.query_one("#cron-validation-lbl", Label)
        explain_static = self.query_one("#cron-explanation", Static)
        table = self.query_one("#cron-runs-table", DataTable)
        table.clear()

        if self.manager.validate(expression):
            valid_lbl.update("[green]Valid Expression[/green]")
            explanation = self.manager.explain(expression)
            explain_static.update(explanation)

            runs = self.manager.get_next_runs(expression, count=5)
            import datetime
            now = datetime.datetime.now()
            for r in runs:
                delta = r - now
                # Simple format
                if delta.days > 0:
                    rel = f"in {delta.days}d {delta.seconds//3600}h"
                elif delta.seconds > 3600:
                    rel = f"in {delta.seconds//3600}h"
                elif delta.seconds > 60:
                    rel = f"in {delta.seconds//60}m"
                else:
                    rel = f"in {delta.seconds}s"

                table.add_row(str(r), rel)
        else:
            valid_lbl.update("[red]Invalid Expression[/red]")
            explain_static.update("Could not parse expression.")

    def generate_expression(self) -> None:
        text = self.query_one("#cron-gen-input", Input).value
        if not text:
            return

        expr = self.manager.generate_from_text(text)
        if expr:
            self.query_one("#cron-input", Input).value = expr
            self.analyze_expression()
            self.notify("Expression generated.")
        else:
            self.notify("Could not generate expression from text.", severity="warning")
