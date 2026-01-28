import re
from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Button, Input, Label, RichLog, Checkbox, TextArea, Select
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from rich.markup import escape

from shared.regex_lab import RegexLabManager

class RegexLabTab(Container):
    """Tab for experimenting with Regex."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = RegexLabManager(project_dir)

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

        flags = 0
        if self.query_one("#chk-ignore-case", Checkbox).value:
            flags |= re.IGNORECASE
        if self.query_one("#chk-multiline", Checkbox).value:
            flags |= re.MULTILINE
        if self.query_one("#chk-dotall", Checkbox).value:
            flags |= re.DOTALL

        result = self.manager.match_regex(pattern, text, flags)

        if "error" in result:
            output.write(f"[bold red]Error:[/bold red] {result['error']}")
            return

        matches = result["matches"]
        if not matches:
            output.write("No matches found.")
            return

        output.write(f"Found [bold green]{len(matches)}[/bold green] matches:\n")

        # Highlight matches in context
        highlighted_text = ""
        last_idx = 0
        for match in matches:
            start, end = match["span"]
            # Append text before match
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
            output.write(f"{i+1}. Span: {match['span']} Group 0: '{match['group_0']}'")
            if match['groups']:
                for j, group in enumerate(match['groups']):
                    output.write(f"   Group {j+1}: '{group}'")

    async def explain_regex(self) -> None:
        pattern = self.query_one("#regex-pattern", Input).value
        if not pattern:
            self.notify("Pattern required.", severity="error")
            return

        agent_type = self.query_one("#regex-agent", Select).value or "gemini"
        output = self.query_one("#regex-output", RichLog)
        output.clear()
        output.write(f"Asking {agent_type} to explain pattern: [bold]{pattern}[/bold]...")

        response = await self.manager.explain_regex(pattern, agent_type)
        output.write("\n[bold green]AI Response:[/bold green]")
        output.write(response)

    async def generate_regex(self) -> None:
        description = self.query_one("#regex-test-string", TextArea).text
        if not description:
            self.notify("Please enter a description in the Test String area.", severity="warning")
            return

        agent_type = self.query_one("#regex-agent", Select).value or "gemini"
        output = self.query_one("#regex-output", RichLog)
        output.clear()
        output.write(f"Asking {agent_type} to generate regex for description...")

        response = await self.manager.generate_regex(description, agent_type)
        output.write("\n[bold green]AI Response:[/bold green]")
        output.write(response)

        # Extract code block
        match = re.search(r"```(?:regex|python)?\s*(.*?)\s*```", response, re.DOTALL)
        if match:
            pattern = match.group(1).strip()
            self.query_one("#regex-pattern", Input).value = pattern
            self.notify("Pattern updated from AI.")
