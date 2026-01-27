from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Label, Button, Input, DataTable, RichLog, Select
from textual.containers import Container, Horizontal, Vertical
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
            yield Label("[bold]Interactive Cron Lab[/bold]", classes="welcome-text")

            # Generator
            with Container(classes="stat-box"):
                yield Label("[bold]Generate from Natural Language[/bold]")
                with Horizontal():
                    yield Input(placeholder="e.g. Every Monday at 9am...", id="cron-gen-input")
                    yield Select.from_values(["gemini", "cursor", "local"], id="cron-agent-select", value="gemini")
                    yield Button("Generate", id="btn-cron-generate", variant="primary")

            # Validator & Calculator
            with Container(classes="stat-box"):
                yield Label("[bold]Expression Validator[/bold]")
                with Horizontal():
                    yield Input(placeholder="* * * * *", id="cron-expression-input")
                    yield Button("Validate & Simulate", id="btn-cron-validate", variant="success")
                    yield Button("Explain (AI)", id="btn-cron-explain", variant="warning")

            # Results
            with Horizontal():
                # Next Runs
                with Vertical(id="cron-next-runs-container", classes="stat-box"):
                    yield Label("[bold]Next 10 Runs[/bold]")
                    yield DataTable(id="cron-runs-table")

                # Explanation
                with Vertical(classes="stat-box"):
                    yield Label("[bold]Explanation / Status[/bold]")
                    yield RichLog(id="cron-log", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        table = self.query_one("#cron-runs-table", DataTable)
        table.add_columns("Run Time", "Day")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cron-validate":
            self.validate_simulate()
        elif event.button.id == "btn-cron-generate":
            await self.generate()
        elif event.button.id == "btn-cron-explain":
            await self.explain()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "cron-expression-input":
            self.validate_simulate()
        elif event.input.id == "cron-gen-input":
            await self.generate()

    def validate_simulate(self) -> None:
        expression = self.query_one("#cron-expression-input", Input).value
        log = self.query_one("#cron-log", RichLog)
        log.clear()

        valid, msg = self.manager.validate(expression)
        if not valid:
            log.write(f"[bold red]Invalid:[/bold red] {msg}")
            self.notify("Invalid expression", severity="error")
            return

        log.write(f"[bold green]Valid:[/bold green] {msg}")

        # Next runs
        runs = self.manager.get_next_runs(expression, count=10)
        table = self.query_one("#cron-runs-table", DataTable)
        table.clear()

        for dt in runs:
            table.add_row(dt.strftime("%Y-%m-%d %H:%M:%S"), dt.strftime("%A"))

    async def generate(self) -> None:
        desc = self.query_one("#cron-gen-input", Input).value
        if not desc:
            self.notify("Description required", severity="error")
            return

        agent = self.query_one("#cron-agent-select", Select).value or "gemini"
        log = self.query_one("#cron-log", RichLog)
        log.clear()
        log.write("Generating...")
        self.notify("Generating...")

        expr = await self.manager.generate_expression(desc, agent_type=agent)

        log.write(f"Generated: [bold]{expr}[/bold]")
        self.query_one("#cron-expression-input", Input).value = expr
        self.validate_simulate()

    async def explain(self) -> None:
        expression = self.query_one("#cron-expression-input", Input).value
        if not expression:
            return

        agent = self.query_one("#cron-agent-select", Select).value or "gemini"
        log = self.query_one("#cron-log", RichLog)
        log.write("\nExplaining...")
        self.notify("Explaining...")

        explanation = await self.manager.explain_expression(expression, agent_type=agent)
        log.write("\n[bold]Explanation:[/bold]")
        log.write(explanation)
