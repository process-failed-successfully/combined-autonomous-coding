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
            yield Label("[bold]Cron Expression Lab[/bold]", classes="welcome-text")

            # Expression Input
            with Container(classes="stat-box"):
                yield Label("Cron Expression:")
                with Horizontal():
                    yield Input(placeholder="e.g. */5 * * * *", id="cron-expression")
                    yield Button("Analyze", id="btn-cron-analyze", variant="primary")

            # AI Helpers
            with Horizontal(classes="stat-box"):
                yield Select.from_values(["gemini", "cursor", "local"], id="cron-agent", value="gemini")
                yield Button("Explain (AI)", id="btn-cron-explain", variant="warning")
                yield Button("Generate from Description (AI)", id="btn-cron-generate", variant="success")

            # Generation Input
            with Vertical(classes="stat-box", id="cron-gen-container"):
                yield Label("Natural Language Description:")
                yield TextArea(id="cron-description")

            # Output
            with Horizontal():
                with VerticalScroll(classes="stat-box", id="cron-next-runs"):
                    yield Label("[bold]Next Runs[/bold]")
                    yield RichLog(id="cron-runs-log", wrap=True, highlight=False, markup=True)

                with VerticalScroll(classes="stat-box", id="cron-output-container"):
                    yield Label("[bold]AI Output[/bold]")
                    yield RichLog(id="cron-ai-log", wrap=True, highlight=False, markup=True)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cron-analyze":
            self.analyze_expression()
        elif event.button.id == "btn-cron-explain":
            await self.explain_expression()
        elif event.button.id == "btn-cron-generate":
            await self.generate_expression()

    def analyze_expression(self) -> None:
        expression = self.query_one("#cron-expression", Input).value
        log = self.query_one("#cron-runs-log", RichLog)
        log.clear()

        if not expression:
            log.write("[red]Error: Expression required.[/red]")
            return

        if self.manager.validate(expression):
            log.write(f"[green]Valid Expression:[/green] {expression}")
            log.write("\n[bold]Next 10 Runs:[/bold]")
            try:
                runs = self.manager.get_next_runs(expression)
                for run in runs:
                    log.write(f"- {run}")
            except Exception as e:
                log.write(f"[red]Error calculating runs: {e}[/red]")
        else:
            log.write(f"[bold red]Invalid Expression:[/bold red] {expression}")

    async def explain_expression(self) -> None:
        expression = self.query_one("#cron-expression", Input).value
        if not expression:
            self.notify("Expression required.", severity="error")
            return

        agent_type = self.query_one("#cron-agent", Select).value or "gemini"
        log = self.query_one("#cron-ai-log", RichLog)
        log.clear()
        log.write(f"Asking {agent_type} to explain: [bold]{expression}[/bold]...")

        try:
            explanation = await self.manager.explain_expression(expression, agent_type)
            log.write("\n[bold green]Explanation:[/bold green]")
            log.write(explanation)
        except Exception as e:
            log.write(f"[bold red]Error:[/bold red] {e}")

    async def generate_expression(self) -> None:
        description = self.query_one("#cron-description", TextArea).text
        if not description:
            self.notify("Description required.", severity="warning")
            return

        agent_type = self.query_one("#cron-agent", Select).value or "gemini"
        log = self.query_one("#cron-ai-log", RichLog)
        log.clear()
        log.write(f"Asking {agent_type} to generate cron for: [italic]{description}[/italic]...")

        try:
            result = await self.manager.generate_expression(description, agent_type)
            log.write("\n[bold green]Result:[/bold green]")
            log.write(result)

            # Try to extract code block to input
            import re
            match = re.search(r"```(?:cron)?\s*(.*?)\s*```", result, re.DOTALL)
            if match:
                expression = match.group(1).strip()
                self.query_one("#cron-expression", Input).value = expression
                self.notify("Expression updated from AI.")
                # Auto-analyze
                self.analyze_expression()

        except Exception as e:
            log.write(f"[bold red]Error:[/bold red] {e}")
