import json
from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Label, Input, RichLog
from textual.containers import Container, Horizontal, Vertical
from textual import on
from shared.levenshtein_lab import LevenshteinLabManager
from rich.syntax import Syntax


class LevenshteinLabTab(Container):
    """
    Interactive Levenshtein evaluator Tab.
    """
    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = LevenshteinLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Levenshtein Distance Calculator[/bold]", classes="welcome-text")

            with Horizontal(classes="stat-box", id="levenshtein-controls"):
                with Vertical():
                    yield Label("String 1:", classes="label")
                    yield Input(placeholder="e.g. kitten", id="levenshtein-str1")
                with Vertical():
                    yield Label("String 2:", classes="label")
                    yield Input(placeholder="e.g. sitting", id="levenshtein-str2")

            with Vertical(classes="stat-box"):
                yield Label("[bold]Results[/bold]")
                yield RichLog(id="levenshtein-results-log", wrap=True, highlight=True, markup=True)

    @on(Input.Changed, "#levenshtein-str1")
    def on_str1_changed(self, event: Input.Changed) -> None:
        self.evaluate_distance()

    @on(Input.Changed, "#levenshtein-str2")
    def on_str2_changed(self, event: Input.Changed) -> None:
        self.evaluate_distance()

    def evaluate_distance(self) -> None:
        str1 = self.query_one("#levenshtein-str1", Input).value
        str2 = self.query_one("#levenshtein-str2", Input).value
        log = self.query_one("#levenshtein-results-log", RichLog)

        log.clear()

        if not str1 and not str2:
            return

        try:
            dist = self.manager.distance(str1, str2)
            sim = self.manager.similarity(str1, str2)

            result = {
                "distance": dist,
                "similarity": f"{sim * 100:.2f}%"
            }

            formatted = json.dumps(result, indent=2)
            syntax = Syntax(formatted, "json", theme="monokai", background_color="default")
            log.write(syntax)
        except Exception as e:
            log.write(f"[bold red]Error calculating distance:[/bold red] {e}")
