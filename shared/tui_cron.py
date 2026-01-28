from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Input, Label, RichLog, Select, DataTable
from textual import on
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

            # Input
            with Horizontal(classes="stat-box"):
                yield Label("Expression:", classes="label")
                yield Input(placeholder="*/5 * * * *", id="cron-input", value="*/5 * * * *")
                yield Button("Validate", id="btn-cron-validate", variant="primary")

            # Status
            yield Label("", id="cron-status-lbl")

            # Explanation
            with Vertical(classes="stat-box"):
                yield Label("[bold]Explanation[/bold]")
                with Horizontal():
                    yield Button("Explain with AI", id="btn-cron-explain", variant="warning")
                    yield Select.from_values(["gemini", "cursor", "local"], id="cron-agent-select", value="gemini")
                yield RichLog(id="cron-explain-log", wrap=True, highlight=True, markup=True)

            # Next Runs
            with Vertical(classes="stat-box"):
                yield Label("[bold]Next 10 Occurrences[/bold]")
                yield DataTable(id="cron-table")

    def on_mount(self) -> None:
        table = self.query_one("#cron-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Count", "Date", "Time")
        self.validate_expression()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cron-validate":
            self.validate_expression()
        elif event.button.id == "btn-cron-explain":
            await self.explain_expression()

    def validate_expression(self) -> None:
        expr = self.query_one("#cron-input", Input).value
        lbl = self.query_one("#cron-status-lbl", Label)

        is_valid, msg = self.manager.validate(expr)

        if is_valid:
            lbl.update(f"[green]✅ {msg}[/green]")
            self.update_next_runs(expr)
        else:
            lbl.update(f"[red]❌ {msg}[/red]")
            self.query_one("#cron-table", DataTable).clear()

    def update_next_runs(self, expr: str) -> None:
        table = self.query_one("#cron-table", DataTable)
        table.clear()

        try:
            occurrences = self.manager.get_next_occurrences(expr, count=10)
            for i, dt in enumerate(occurrences):
                table.add_row(str(i+1), dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M:%S"))
        except Exception as e:
            self.notify(f"Calculation error: {e}", severity="error")

    async def explain_expression(self) -> None:
        expr = self.query_one("#cron-input", Input).value
        is_valid, _ = self.manager.validate(expr)
        if not is_valid:
            self.notify("Invalid expression.", severity="error")
            return

        agent = self.query_one("#cron-agent-select", Select).value or "gemini"
        log = self.query_one("#cron-explain-log", RichLog)

        log.clear()
        log.write(f"Asking {agent} to explain '{expr}'...")
        self.notify("Generating explanation...")

        import asyncio
        response = await self.manager.explain_expression(expr, agent_type=agent)

        log.clear()
        log.write(response)
        self.notify("Explanation received.")
