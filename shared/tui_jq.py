import json
from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Label, Input, TextArea, RichLog
from textual.containers import Container, Horizontal, Vertical
from textual import on
from shared.jq_lab import JqLabManager
from rich.syntax import Syntax


class JqLabTab(Container):
    """
    Interactive jq evaluator Tab.
    """
    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = JqLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]jq Evaluator[/bold]", classes="welcome-text")

            with Horizontal(classes="stat-box", id="jq-controls"):
                yield Label("jq Filter:", classes="label")
                yield Input(placeholder="e.g. .store.book[].author", id="jq-input")

            with Horizontal():
                with Vertical(classes="stat-box"):
                    yield Label("[bold]Input JSON[/bold]")
                    yield TextArea(
                        '{\n  "store": {\n    "book": [\n      { "title": "A", "author": "Alice" },\n      { "title": "B", "author": "Bob" }\n    ]\n  }\n}',
                        language="json",
                        id="jq-input-json"
                    )

                with Vertical(classes="stat-box"):
                    yield Label("[bold]Results[/bold]")
                    yield RichLog(id="jq-results-log", wrap=True, highlight=True, markup=True)

    @on(Input.Changed, "#jq-input")
    def on_expression_changed(self, event: Input.Changed) -> None:
        self.evaluate_path()

    @on(TextArea.Changed, "#jq-input-json")
    def on_json_changed(self, event: TextArea.Changed) -> None:
        self.evaluate_path()

    def evaluate_path(self) -> None:
        json_text = self.query_one("#jq-input-json", TextArea).text
        path_expr = self.query_one("#jq-input", Input).value
        log = self.query_one("#jq-results-log", RichLog)

        log.clear()

        if not json_text.strip():
            return

        if not path_expr.strip():
            return

        try:
            data = json.loads(json_text)
        except json.JSONDecodeError as e:
            log.write(f"[bold red]Invalid JSON:[/bold red] {e}")
            return

        try:
            results = self.manager.evaluate(data, path_expr)
            if results is None:
                log.write("[italic]No matches found.[/italic]")
            else:
                formatted = json.dumps(results, indent=2)
                syntax = Syntax(formatted, "json", theme="monokai", background_color="default")
                log.write(syntax)
        except Exception as e:
            log.write(f"[bold red]Error evaluating jq:[/bold red] {e}")
