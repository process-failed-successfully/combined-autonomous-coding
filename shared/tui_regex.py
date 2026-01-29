import re
import io
import contextlib
from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Button, Input, Label, RichLog, Checkbox, TextArea, Select, TabbedContent, TabPane
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual import on
from rich.markup import escape

from shared.ask import run_ask_logic
from shared.regex_game import RegexGameEngine, RegexGameGenerator

class RegexLabTab(Container):
    """Tab for experimenting with Regex."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.game_generator = RegexGameGenerator()
        self.game_engine = RegexGameEngine()
        self.current_level_index = 0
        self.levels = self.game_generator.generate_levels()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Regex Lab[/bold]", classes="welcome-text")

            with TabbedContent():
                with TabPane("Playground"):
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

                with TabPane("Game Mode"):
                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Regex Golf[/bold]", classes="welcome-text")
                        yield Label("", id="game-level-name")
                        yield Label("", id="game-level-description")

                        with Horizontal():
                            yield Input(placeholder="Enter regex...", id="game-input")
                            yield Button("Submit", id="btn-game-submit", variant="primary")
                            yield Button("Next Level", id="btn-game-next", variant="success", disabled=True)
                            yield Button("Hint (AI)", id="btn-game-hint", variant="warning")

                        yield Label("[bold]Test Cases[/bold]")
                        yield RichLog(id="game-feedback", wrap=True, highlight=False, markup=True)

    def on_mount(self) -> None:
        self.load_level()

    def load_level(self) -> None:
        if self.current_level_index < len(self.levels):
            level = self.levels[self.current_level_index]
            self.query_one("#game-level-name", Label).update(f"[bold]{level.name}[/bold]")
            self.query_one("#game-level-description", Label).update(level.description)
            self.query_one("#game-input", Input).value = ""
            self.query_one("#btn-game-next").disabled = True

            feedback = self.query_one("#game-feedback", RichLog)
            feedback.clear()
            feedback.write("[bold green]Positive Cases (Must Match):[/bold green]")
            for case in level.positive_cases:
                feedback.write(f"  - {case}")
            feedback.write("\n[bold red]Negative Cases (Must NOT Match):[/bold red]")
            for case in level.negative_cases:
                feedback.write(f"  - {case}")
        else:
            self.query_one("#game-level-name", Label).update("[bold]All levels completed![/bold]")
            self.query_one("#game-level-description", Label).update("Congratulations! You have mastered regex.")
            self.query_one("#game-input", Input).disabled = True
            self.query_one("#btn-game-submit").disabled = True

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-regex-match":
            self.match_regex()
        elif event.button.id == "btn-regex-explain":
            await self.explain_regex()
        elif event.button.id == "btn-regex-generate":
            await self.generate_regex()
        elif event.button.id == "btn-game-submit":
            self.check_game_answer()
        elif event.button.id == "btn-game-next":
            self.current_level_index += 1
            self.load_level()
        elif event.button.id == "btn-game-hint":
            await self.get_hint()

    def check_game_answer(self) -> None:
        pattern = self.query_one("#game-input", Input).value
        if not pattern:
            self.notify("Please enter a regex pattern.", severity="error")
            return

        level = self.levels[self.current_level_index]
        result = self.game_engine.validate(pattern, level)

        feedback = self.query_one("#game-feedback", RichLog)
        feedback.clear()

        if result.get("error"):
            feedback.write(f"[bold red]Error:[/bold red] {result['error']}")
            return

        feedback.write("[bold]Validation Results:[/bold]\n")

        # Positive Cases
        feedback.write("[bold green]Positive Cases:[/bold green]")
        for case, passed in result["positive_results"]:
            icon = "✅" if passed else "❌"
            feedback.write(f"{icon} '{case}'")

        # Negative Cases
        feedback.write("\n[bold red]Negative Cases:[/bold red]")
        for case, passed in result["negative_results"]:
            icon = "✅" if passed else "❌"
            feedback.write(f"{icon} '{case}' (Should NOT match)")

        if result["success"]:
            feedback.write("\n[bold green]Level Passed![/bold green]")
            self.notify("Correct!")
            self.query_one("#btn-game-next").disabled = False
        else:
            feedback.write("\n[bold red]Try Again.[/bold red]")
            self.notify("Incorrect.", severity="error")

    async def get_hint(self) -> None:
        level = self.levels[self.current_level_index]
        agent_type = "gemini" # Default or user choice

        prompt = f"""
I am trying to solve a regex puzzle.
Goal: {level.description}
Must match: {level.positive_cases}
Must NOT match: {level.negative_cases}

Give me a hint about what regex concepts I should use. Do not give me the exact answer.
"""
        feedback = self.query_one("#game-feedback", RichLog)
        feedback.write("\n[italic]Asking AI for a hint...[/italic]")

        output_capture = io.StringIO()
        try:
            with contextlib.redirect_stdout(output_capture):
                await run_ask_logic(
                    query=prompt,
                    project_dir=self.project_dir,
                    agent_type=agent_type,
                    verbose=False
                )
            hint = output_capture.getvalue()
            feedback.write(f"\n[bold yellow]Hint:[/bold yellow] {hint}")
        except Exception as e:
            feedback.write(f"\n[bold red]Hint Error:[/bold red] {e}")

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
