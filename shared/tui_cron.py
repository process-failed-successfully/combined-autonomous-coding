import re
import io
import contextlib
from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Button, Input, Label, RichLog, Select, TextArea
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
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

            # Calculator Section
            with Container(classes="stat-box"):
                yield Label("Cron Expression:")
                with Horizontal():
                    yield Input(placeholder="e.g. */5 * * * *", id="cron-input")
                    yield Button("Calculate Next Runs", id="btn-cron-calc", variant="primary")

            # AI Helpers
            with Horizontal(classes="stat-box"):
                yield Select.from_values(["gemini", "cursor", "local"], id="cron-agent", value="gemini")
                yield Button("Explain (AI)", id="btn-cron-explain", variant="warning")
                yield Button("Generate from Description (AI)", id="btn-cron-generate", variant="success")

            # Description Input (for generation)
            with Vertical(classes="stat-box", id="cron-desc-container"):
                yield Label("Description / Schedule Requirements:")
                yield TextArea(id="cron-desc-input")

            # Output
            with VerticalScroll(classes="stat-box", id="cron-output-container"):
                yield Label("[bold]Results[/bold]")
                yield RichLog(id="cron-output", wrap=True, highlight=False, markup=True)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cron-calc":
            self.calculate_runs()
        elif event.button.id == "btn-cron-explain":
            await self.explain_cron()
        elif event.button.id == "btn-cron-generate":
            await self.generate_cron()

    def calculate_runs(self) -> None:
        expression = self.query_one("#cron-input", Input).value
        output = self.query_one("#cron-output", RichLog)
        output.clear()

        if not expression:
            output.write("[red]Error: Expression required.[/red]")
            return

        result = self.manager.get_next_runs(expression, count=10)

        if result["success"]:
            output.write(f"Expression: [bold blue]{result['expression']}[/bold blue]")
            output.write(f"Base Time: {result['base_time']}")
            output.write("\n[bold green]Next 10 Runs:[/bold green]")
            for dt in result["next_runs"]:
                output.write(f"  {dt}")
        else:
            output.write(f"[bold red]Error:[/bold red] {result['error']}")

    async def explain_cron(self) -> None:
        expression = self.query_one("#cron-input", Input).value
        output = self.query_one("#cron-output", RichLog)
        output.clear()

        if not expression:
            self.notify("Expression required.", severity="error")
            return

        agent_type = self.query_one("#cron-agent", Select).value or "gemini"
        output.write(f"Asking {agent_type} to explain: [bold]{expression}[/bold]...")

        response = await self.manager.explain_expression(expression, agent_type)
        output.write("\n[bold green]Explanation:[/bold green]")
        output.write(response)

    async def generate_cron(self) -> None:
        description = self.query_one("#cron-desc-input", TextArea).text
        output = self.query_one("#cron-output", RichLog)
        output.clear()

        if not description:
            self.notify("Description required.", severity="warning")
            return

        agent_type = self.query_one("#cron-agent", Select).value or "gemini"
        output.write(f"Asking {agent_type} to generate expression...")

        response = await self.manager.generate_expression(description, agent_type)

        output.write("\n[bold green]AI Response:[/bold green]")
        output.write(response)

        # Try to extract code block to input
        match = re.search(r"```(?:\w+)?\s*(.*?)\s*```", response, re.DOTALL)
        if match:
            expression = match.group(1).strip()
            # Basic validation: ensure it has at least 5 parts
            if len(expression.split()) >= 5:
                self.query_one("#cron-input", Input).value = expression
                self.notify("Expression updated from AI.")
