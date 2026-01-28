from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Button, Input, Label, RichLog, Select
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual import on
from shared.cron_lab import CronLabManager
import re

class CronLabTab(Container):
    """Tab for experimenting with Cron expressions."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = CronLabManager(project_dir)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Cron Lab[/bold]", classes="welcome-text")

            # Expression Input
            with Container(classes="stat-box"):
                yield Label("Cron Expression:")
                with Horizontal():
                    yield Input(placeholder="e.g. */5 * * * *", id="cron-expression")
                    yield Button("Validate & Next", id="btn-cron-validate", variant="primary")
                    yield Button("Explain (AI)", id="btn-cron-explain", variant="warning")

            # Generation
            with Container(classes="stat-box"):
                yield Label("Generate from Description (AI):")
                with Horizontal():
                    yield Input(placeholder="e.g. Every Monday at 9am", id="cron-description")
                    yield Button("Generate", id="btn-cron-generate", variant="success")
                yield Select.from_values(["gemini", "cursor", "local"], id="cron-agent", value="gemini")

            # Output
            with VerticalScroll(classes="stat-box", id="cron-output-container"):
                yield Label("[bold]Results[/bold]")
                yield RichLog(id="cron-output", wrap=True, highlight=False, markup=True)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cron-validate":
            self.validate_expression()
        elif event.button.id == "btn-cron-explain":
            await self.explain_expression()
        elif event.button.id == "btn-cron-generate":
            await self.generate_expression()

    def validate_expression(self) -> None:
        expression = self.query_one("#cron-expression", Input).value
        output = self.query_one("#cron-output", RichLog)
        output.clear()

        valid, message = self.manager.validate(expression)

        if valid:
            output.write(f"[bold green]Valid Expression:[/bold green] {expression}")
            output.write(f"\n[bold]Next 5 Occurrences:[/bold]")
            try:
                next_runs = self.manager.get_next_occurrences(expression)
                for dt in next_runs:
                    output.write(f"  - {dt}")
            except Exception as e:
                output.write(f"[red]Error calculating next runs: {e}[/red]")
        else:
            output.write(f"[bold red]Invalid Expression:[/bold red] {expression}")
            output.write(f"Reason: {message}")

    async def explain_expression(self) -> None:
        expression = self.query_one("#cron-expression", Input).value
        output = self.query_one("#cron-output", RichLog)
        agent_type = self.query_one("#cron-agent", Select).value or "gemini"

        if not expression:
            self.notify("Expression required.", severity="error")
            return

        output.clear()
        output.write(f"Asking {agent_type} to explain: [bold]{expression}[/bold]...")

        explanation = await self.manager.explain(expression, agent_type=agent_type)
        output.write("\n[bold green]Explanation:[/bold green]")
        output.write(explanation)

    async def generate_expression(self) -> None:
        description = self.query_one("#cron-description", Input).value
        output = self.query_one("#cron-output", RichLog)
        agent_type = self.query_one("#cron-agent", Select).value or "gemini"

        if not description:
            self.notify("Description required.", severity="warning")
            return

        output.clear()
        output.write(f"Asking {agent_type} to generate cron for: [bold]{description}[/bold]...")

        result = await self.manager.generate(description, agent_type=agent_type)
        output.write("\n[bold green]Result:[/bold green]")
        output.write(result)

        # Try to extract code block
        match = re.search(r"`([^`]+)`", result)
        if match:
            potential_cron = match.group(1).strip()
            self.query_one("#cron-expression", Input).value = potential_cron
            self.notify("Expression updated from AI.")
