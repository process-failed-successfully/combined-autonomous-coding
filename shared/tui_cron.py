import io
import contextlib
from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Button, Input, Label, RichLog, TextArea, Select
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual import on

from shared.ask import run_ask_logic
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

            # Calculator Section
            with Container(classes="stat-box"):
                yield Label("Cron Expression:")
                with Horizontal():
                    yield Input(placeholder="e.g. */5 * * * *", id="cron-expression")
                    yield Input(placeholder="Count", id="cron-count", value="5", type="integer")
                    yield Button("Calculate Next", id="btn-cron-next", variant="primary")

            # AI Helpers
            with Horizontal(classes="stat-box"):
                yield Select.from_values(["gemini", "cursor", "local"], id="cron-agent", value="gemini")
                yield Button("Explain (AI)", id="btn-cron-explain", variant="warning")
                yield Button("Generate (AI)", id="btn-cron-generate", variant="success")

            # Description Input
            with Vertical(classes="stat-box"):
                yield Label("Description (for generation):")
                yield TextArea(id="cron-description")

            # Output
            with VerticalScroll(classes="stat-box", id="cron-output-container"):
                yield Label("[bold]Results[/bold]")
                yield RichLog(id="cron-output", wrap=True, highlight=True, markup=True)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cron-next":
            self.calculate_next()
        elif event.button.id == "btn-cron-explain":
            await self.explain_cron()
        elif event.button.id == "btn-cron-generate":
            await self.generate_cron()

    def calculate_next(self) -> None:
        expression = self.query_one("#cron-expression", Input).value
        count_val = self.query_one("#cron-count", Input).value
        count = int(count_val) if count_val.isdigit() else 5

        output = self.query_one("#cron-output", RichLog)
        output.clear()

        if not expression:
            self.notify("Cron expression required.", severity="error")
            return

        result = self.manager.get_next_occurrences(expression, count)

        if result["success"]:
            output.write(f"[bold green]Next {count} occurrences for '{expression}':[/bold green]")
            for occ in result["occurrences"]:
                output.write(f"  - {occ}")
        else:
            output.write(f"[bold red]Error:[/bold red] {result['error']}")
            self.notify("Invalid cron expression.", severity="error")

    async def explain_cron(self) -> None:
        expression = self.query_one("#cron-expression", Input).value
        if not expression:
            self.notify("Cron expression required.", severity="error")
            return

        agent_type = self.query_one("#cron-agent", Select).value or "gemini"
        output = self.query_one("#cron-output", RichLog)
        output.clear()
        output.write(f"Asking {agent_type} to explain: [bold]{expression}[/bold]...")

        prompt = f"Explain the following cron expression in plain English:\n\n```\n{expression}\n```"
        await self._run_ai(prompt, agent_type, output)

    async def generate_cron(self) -> None:
        description = self.query_one("#cron-description", TextArea).text
        if not description:
            self.notify("Description required.", severity="error")
            return

        agent_type = self.query_one("#cron-agent", Select).value or "gemini"
        output = self.query_one("#cron-output", RichLog)
        output.clear()
        output.write(f"Asking {agent_type} to generate cron expression...")

        prompt = f"Generate a standard cron expression for the following schedule description. Provide only the cron expression first, wrapped in code blocks, followed by a brief explanation.\n\nDescription:\n{description}"
        await self._run_ai(prompt, agent_type, output)

    async def _run_ai(self, prompt: str, agent_type: str, log: RichLog) -> None:
        output_capture = io.StringIO()
        try:
            with contextlib.redirect_stdout(output_capture):
                await run_ask_logic(
                    query=prompt,
                    project_dir=self.project_dir,
                    agent_type=agent_type,
                    verbose=False
                )

            response = output_capture.getvalue()
            log.write("\n[bold green]AI Response:[/bold green]")
            log.write(response)

            # If generating, try to extract code block to input
            import re
            if "Generate" in str(prompt): # Simple heuristic
                match = re.search(r"```(?:cron)?\s*(.*?)\s*```", response, re.DOTALL)
                if match:
                    expression = match.group(1).strip()
                    # Filter out non-cron characters if it's too verbose
                    lines = expression.splitlines()
                    if lines:
                        expression = lines[0].strip()

                    self.query_one("#cron-expression", Input).value = expression
                    self.notify("Expression updated from AI.")

        except Exception as e:
            log.write(f"[bold red]AI Error:[/bold red] {e}")
