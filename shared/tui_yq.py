import yaml
from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Label, Input, TextArea, RichLog
from textual.containers import Container, Horizontal, Vertical
from textual import on
from shared.yq_lab import YqLabManager
from rich.syntax import Syntax


class YqLabTab(Container):
    """
    Interactive yq evaluator Tab.
    """
    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = YqLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]yq Evaluator[/bold]", classes="welcome-text")

            with Horizontal(classes="stat-box", id="yq-controls"):
                yield Label("jq Filter:", classes="label")
                yield Input(placeholder="e.g. .store.book[].author", id="yq-input")

            with Horizontal():
                with Vertical(classes="stat-box"):
                    yield Label("[bold]Input YAML[/bold]")
                    yield TextArea(
                        'store:\n  book:\n    - title: "A"\n      author: "Alice"\n    - title: "B"\n      author: "Bob"',
                        language="yaml",
                        id="yq-input-yaml"
                    )

                with Vertical(classes="stat-box"):
                    yield Label("[bold]Results[/bold]")
                    yield RichLog(id="yq-results-log", wrap=True, highlight=True, markup=True)

    @on(Input.Changed, "#yq-input")
    def on_expression_changed(self, event: Input.Changed) -> None:
        self.evaluate_path()

    @on(TextArea.Changed, "#yq-input-yaml")
    def on_yaml_changed(self, event: TextArea.Changed) -> None:
        self.evaluate_path()

    def evaluate_path(self) -> None:
        yaml_text = self.query_one("#yq-input-yaml", TextArea).text
        path_expr = self.query_one("#yq-input", Input).value
        log = self.query_one("#yq-results-log", RichLog)

        log.clear()

        if not yaml_text.strip():
            return

        if not path_expr.strip():
            return

        try:
            data = yaml.safe_load(yaml_text)
        except yaml.YAMLError as e:
            log.write(f"[bold red]Invalid YAML:[/bold red] {e}")
            return

        try:
            results = self.manager.evaluate(data, path_expr)
            if results is None:
                log.write("[italic]No matches found.[/italic]")
            else:
                if isinstance(results, (dict, list)):
                    formatted = yaml.safe_dump(results, default_flow_style=False, sort_keys=False).strip()
                    syntax = Syntax(formatted, "yaml", theme="monokai", background_color="default")
                    log.write(syntax)
                else:
                    log.write(str(results))
        except Exception as e:
            log.write(f"[bold red]Error evaluating yq:[/bold red] {e}")
