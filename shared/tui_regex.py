import re
import io
import contextlib
from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Button, Input, Label, RichLog, Checkbox, TextArea, Select
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual import on
from rich.markup import escape

from shared.ask import run_ask_logic

class RegexLabTab(Container):
    """Tab for experimenting with Regex."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Regex Lab[/bold]", classes="welcome-text")

            # Pattern Input
            with Container(classes="stat-box"):
                yield Label("Regex Pattern:")
                with Horizontal():
                    yield Input(placeholder="e.g. ^[a-zA-Z0-9]+$", id="regex-pattern")
                    yield Button("Match", id="btn-regex-match", variant="primary")

                with Horizontal():
                    yield Checkbox("Ignore Case", id="chk-ignore-case")
                    yield Checkbox("Multiline", id="chk-multiline")
                    yield Checkbox("Dot All", id="chk-dotall")

            # AI Helpers
            with Horizontal(classes="stat-box"):
                yield Select.from_values(["gemini", "cursor", "local"], id="regex-agent", value="gemini")
                yield Button("Explain Pattern (AI)", id="btn-regex-explain", variant="warning")
                yield Button("Generate from Description (AI)", id="btn-regex-generate", variant="success")

            # Test String
            with Vertical(classes="stat-box", id="regex-test-container"):
                yield Label("Test String:")
                yield TextArea(id="regex-test-string")

            # Output
            with VerticalScroll(classes="stat-box", id="regex-output-container"):
                yield Label("[bold]Results[/bold]")
                yield RichLog(id="regex-output", wrap=True, highlight=False, markup=True)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-regex-match":
            self.match_regex()
        elif event.button.id == "btn-regex-explain":
            await self.explain_regex()
        elif event.button.id == "btn-regex-generate":
            await self.generate_regex()

    def match_regex(self) -> None:
        pattern = self.query_one("#regex-pattern", Input).value
        text = self.query_one("#regex-test-string", TextArea).text
        output = self.query_one("#regex-output", RichLog)
        output.clear()

        if not pattern:
            output.write("[red]Error: Pattern required.[/red]")
            return

        flags = 0
        if self.query_one("#chk-ignore-case", Checkbox).value:
            flags |= re.IGNORECASE
        if self.query_one("#chk-multiline", Checkbox).value:
            flags |= re.MULTILINE
        if self.query_one("#chk-dotall", Checkbox).value:
            flags |= re.DOTALL

        try:
            matches = list(re.finditer(pattern, text, flags))
            if not matches:
                output.write("No matches found.")
                return

            output.write(f"Found [bold green]{len(matches)}[/bold green] matches:\n")

            # Highlight matches in context
            # We can construct a highlighted string or just list matches.
            # A highlighted string is nicer.

            highlighted_text = ""
            last_idx = 0
            for match in matches:
                start, end = match.span()
                # Append text before match
                # Escape user text to prevent markup injection
                highlighted_text += escape(text[last_idx:start])

                # Append highlighted match
                matched_str = escape(text[start:end])
                highlighted_text += f"[bold magenta reverse]{matched_str}[/bold magenta reverse]"
                last_idx = end

            # Append remaining text
            highlighted_text += escape(text[last_idx:])

            output.write(highlighted_text)

            output.write("\n[bold]Details:[/bold]")
            for i, match in enumerate(matches):
                output.write(f"{i+1}. Span: {match.span()} Group 0: '{match.group(0)}'")
                # Show groups if any
                if match.groups():
                    for j, group in enumerate(match.groups()):
                        output.write(f"   Group {j+1}: '{group}'")

        except re.error as e:
            output.write(f"[bold red]Regex Error:[/bold red] {e}")

    async def explain_regex(self) -> None:
        pattern = self.query_one("#regex-pattern", Input).value
        if not pattern:
            self.notify("Pattern required.", severity="error")
            return

        agent_type = self.query_one("#regex-agent", Select).value or "gemini"
        output = self.query_one("#regex-output", RichLog)
        output.clear()
        output.write(f"Asking {agent_type} to explain pattern: [bold]{pattern}[/bold]...")

        prompt = f"Explain the following regex pattern in detail:\n\n```regex\n{pattern}\n```"

        await self._run_ai(prompt, agent_type, output)

    async def generate_regex(self) -> None:
        description = self.query_one("#regex-test-string", TextArea).text
        if not description:
            self.notify("Please enter a description in the Test String area.", severity="warning")
            return

        agent_type = self.query_one("#regex-agent", Select).value or "gemini"
        output = self.query_one("#regex-output", RichLog)
        output.clear()
        output.write(f"Asking {agent_type} to generate regex for description...")

        prompt = f"Generate a Python regex pattern for the following description. Provide only the regex pattern first, wrapped in code blocks, followed by a brief explanation.\n\nDescription:\n{description}"

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
            if "Generate" in str(prompt): # Simple heuristic
                match = re.search(r"```(?:regex|python)?\s*(.*?)\s*```", response, re.DOTALL)
                if match:
                    pattern = match.group(1).strip()
                    self.query_one("#regex-pattern", Input).value = pattern
                    self.notify("Pattern updated from AI.")

        except Exception as e:
            log.write(f"[bold red]AI Error:[/bold red] {e}")
