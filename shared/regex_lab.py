import re
import sys
import io
import contextlib
from pathlib import Path
from typing import Optional, Dict, Any, List
from shared.ask import run_ask_logic
from shared.regex_game import RegexGameGenerator, RegexGameEngine

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    console = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    console = None

class RegexLabManager:
    """Manages Regex Lab operations: matching, explaining, and generating."""

    def match_regex(self, pattern: str, text: str, flags: int = 0) -> Dict[str, Any]:
        """
        Matches a regex pattern against text.

        Args:
            pattern: The regex pattern.
            text: The text to search.
            flags: Regex flags (e.g. re.IGNORECASE).

        Returns:
            Dict containing match results.
        """
        try:
            matches = list(re.finditer(pattern, text, flags))
            results: List[Dict[str, Any]] = []

            for i, match in enumerate(matches):
                match_info = {
                    "index": i + 1,
                    "span": match.span(),
                    "full_match": match.group(0),
                    "groups": match.groups(),
                    "group_dict": match.groupdict()
                }
                results.append(match_info)

            return {
                "success": True,
                "count": len(matches),
                "matches": results
            }
        except re.error as e:
            return {
                "success": False,
                "error": str(e)
            }

    def extract_regex(self, pattern: str, text: str, flags: int = 0) -> Dict[str, Any]:
        """
        Extracts all matches of a regex pattern from text.

        Args:
            pattern: The regex pattern.
            text: The text to search.
            flags: Regex flags (e.g. re.IGNORECASE).

        Returns:
            Dict containing the list of extracted matching strings.
        """
        try:
            matches = list(re.finditer(pattern, text, flags))
            results: List[str] = [match.group(0) for match in matches]

            return {
                "success": True,
                "count": len(results),
                "matches": results
            }
        except re.error as e:
            return {
                "success": False,
                "error": str(e)
            }

    def replace_regex(self, pattern: str, replacement: str, text: str, flags: int = 0) -> Dict[str, Any]:
        """
        Replaces text matching a regex pattern.

        Args:
            pattern: The regex pattern.
            replacement: The replacement string.
            text: The text to search.
            flags: Regex flags (e.g. re.IGNORECASE).

        Returns:
            Dict containing replacement results.
        """
        try:
            new_text, count = re.subn(pattern, replacement, text, flags=flags)
            return {
                "success": True,
                "original_text": text,
                "modified_text": new_text,
                "count": count
            }
        except re.error as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def explain_regex(self, pattern: str, project_dir: Path, agent_type: str = "gemini", model: Optional[str] = None) -> bool:
        """
        Explains a regex pattern using AI.
        """
        prompt = f"Explain the following regex pattern in detail:\n\n```regex\n{pattern}\n```"
        return await run_ask_logic(
            query=prompt,
            project_dir=project_dir,
            agent_type=agent_type,
            model=model,
            verbose=False
        )

    async def generate_regex(self, description: str, project_dir: Path, agent_type: str = "gemini", model: Optional[str] = None) -> bool:
        """
        Generates a regex pattern from a description using AI.
        """
        prompt = f"Generate a Python regex pattern for the following description. Provide only the regex pattern first, wrapped in code blocks, followed by a brief explanation.\n\nDescription:\n{description}"
        return await run_ask_logic(
            query=prompt,
            project_dir=project_dir,
            agent_type=agent_type,
            model=model,
            verbose=False
        )

    async def get_ai_hint(self, description: str, positive_cases: list, negative_cases: list, project_dir: Path, agent_type: str = "gemini", model: Optional[str] = None) -> str:
        """
        Generates a hint using AI without giving the exact answer.
        """
        prompt = f"""
I am playing a regex game and I am stuck.
Goal: {description}
Must match these strings: {positive_cases}
Must NOT match these strings: {negative_cases}

Give me a hint about what regex concepts or constructs I should use to solve this.
Do NOT give me the exact regex pattern. Keep it brief and helpful.
"""
        # Capture stdout because run_ask_logic prints to stdout
        output_capture = io.StringIO()
        try:
            with contextlib.redirect_stdout(output_capture):
                await run_ask_logic(
                    query=prompt,
                    project_dir=project_dir,
                    agent_type=agent_type,
                    model=model,
                    verbose=False
                )
            return output_capture.getvalue()
        except Exception as e:
            return f"Error getting hint: {e}"


async def run_regex_game_cli(project_dir: Path, agent_type: str = "gemini", model: Optional[str] = None):
    """
    Runs the interactive Regex Game in the CLI.
    """
    generator = RegexGameGenerator()
    engine = RegexGameEngine()
    manager = RegexLabManager()
    levels = generator.generate_levels()

    print("\n🎮 Welcome to the Regex Game! 🎮\n")
    print("Commands:")
    print("  <regex> : Test a pattern")
    print("  hint    : Get an AI hint")
    print("  skip    : Skip to next level")
    print("  quit    : Exit game\n")

    for i, level in enumerate(levels):
        title = f"Level {i+1}: {level.name}"
        if HAS_RICH and console:
            console.rule(f"[bold cyan]{title}[/bold cyan]")
            console.print(f"[italic]{level.description}[/italic]\n")

            grid = Table.grid(expand=True)
            grid.add_column()
            grid.add_column()

            pos_text = "\n".join([f"[green]✔ {case}[/green]" for case in level.positive_cases])
            neg_text = "\n".join([f"[red]✘ {case}[/red]" for case in level.negative_cases])

            console.print(Panel(pos_text, title="[bold green]Must Match[/bold green]", border_style="green"))
            console.print(Panel(neg_text, title="[bold red]Must NOT Match[/bold red]", border_style="red"))
        else:
            print(f"--- {title} ---")
            print(f"Goal: {level.description}")
            print("Must Match:     " + ", ".join(level.positive_cases))
            print("Must NOT Match: " + ", ".join(level.negative_cases))
            print("-" * 30)

        while True:
            try:
                user_input = input("\nEnter regex > ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nExiting game.")
                return

            if not user_input:
                continue

            if user_input.lower() == "quit":
                print("Thanks for playing!")
                return

            if user_input.lower() == "skip":
                print("Skipping level...")
                break

            if user_input.lower() == "hint":
                print("\nThinking... 🤖")
                hint = await manager.get_ai_hint(
                    level.description,
                    level.positive_cases,
                    level.negative_cases,
                    project_dir,
                    agent_type,
                    model
                )
                if HAS_RICH and console:
                    console.print(Panel(hint, title="AI Hint", border_style="yellow"))
                else:
                    print(f"\n--- Hint ---\n{hint}\n------------")
                continue

            # Validate
            result = engine.validate(user_input, level)

            if result.get("error"):
                print(f"❌ Error: {result['error']}")
                continue

            # Display Results
            if HAS_RICH and console:
                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("Case")
                table.add_column("Type")
                table.add_column("Status")

                for case, passed in result["positive_results"]:
                    status = "[green]PASS[/green]" if passed else "[red]FAIL[/red]"
                    table.add_row(case, "Positive", status)

                for case, passed in result["negative_results"]:
                    status = "[green]PASS[/green]" if passed else "[red]FAIL[/red]"
                    table.add_row(case, "Negative", status)

                console.print(table)
            else:
                for case, passed in result["positive_results"]:
                    status = "PASS" if passed else "FAIL"
                    print(f"  [+] {case}: {status}")
                for case, passed in result["negative_results"]:
                    status = "PASS" if passed else "FAIL"
                    print(f"  [-] {case}: {status}")

            if result["success"]:
                print("\n🎉 Level Cleared! 🎉")
                break
            else:
                print("\nTry again.")

    print("\n🏆 Congratulations! You have completed all levels! 🏆")
