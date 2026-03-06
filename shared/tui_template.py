import json
import yaml
from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Label, TextArea, RichLog
from textual.containers import Container, Horizontal, Vertical
from textual import on, work
from rich.syntax import Syntax
from shared.template_lab import TemplateLabManager


class TemplateLabTab(Container):
    """
    Interactive Jinja2 Template Evaluator Tab.
    """
    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = TemplateLabManager(self.project_dir)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Jinja2 Template Lab[/bold]", classes="welcome-text")

            with Horizontal():
                with Vertical(classes="stat-box"):
                    yield Label("[bold]Template (Jinja2)[/bold]")
                    yield TextArea(
                        "Hello {{ user.name }}!\nWelcome to {{ project }}.",
                        language="html",
                        id="template-input"
                    )

                with Vertical(classes="stat-box"):
                    yield Label("[bold]Data (JSON/YAML)[/bold]")
                    yield TextArea(
                        '{\n  "user": {\n    "name": "Alice"\n  },\n  "project": "Template Lab"\n}',
                        language="json",
                        id="template-data-input"
                    )

            with Vertical(classes="stat-box"):
                yield Label("[bold]Rendered Output[/bold]")
                yield RichLog(id="template-results-log", wrap=True, highlight=True, markup=True)

    @on(TextArea.Changed, "#template-input")
    def on_template_changed(self, event: TextArea.Changed) -> None:
        template_text = self.query_one("#template-input", TextArea).text
        data_text = self.query_one("#template-data-input", TextArea).text
        self.evaluate_template(template_text, data_text)

    @on(TextArea.Changed, "#template-data-input")
    def on_data_changed(self, event: TextArea.Changed) -> None:
        template_text = self.query_one("#template-input", TextArea).text
        data_text = self.query_one("#template-data-input", TextArea).text
        self.evaluate_template(template_text, data_text)

    @work(exclusive=True, thread=True)
    def evaluate_template(self, template_text: str, data_text: str) -> None:
        if not template_text.strip():
            self.app.call_from_thread(self._update_log, "")
            return

        data = {}
        if data_text.strip():
            try:
                data = json.loads(data_text)
            except json.JSONDecodeError:
                try:
                    parsed_yaml = yaml.safe_load(data_text)
                    if isinstance(parsed_yaml, dict):
                        data = parsed_yaml
                    else:
                        raise ValueError("Data must be a dictionary")
                except Exception as e:
                    self.app.call_from_thread(self._update_log, f"[bold red]Invalid Data (JSON/YAML):[/bold red] {e}")
                    return

        try:
            # We bypass the manager's file requirement by rendering text directly using the env
            # The manager's self.env is set up properly with the project path.
            template = self.manager.env.from_string(template_text)
            rendered = template.render(**data)

            # Syntax highlighting if HTML
            syntax = Syntax(rendered, "html", theme="monokai", background_color="default")
            self.app.call_from_thread(self._update_log, syntax)
        except Exception as e:
            self.app.call_from_thread(self._update_log, f"[bold red]Error rendering template:[/bold red] {e}")

    def _update_log(self, content: any) -> None:
        log = self.query_one("#template-results-log", RichLog)
        log.clear()
        if content:
            log.write(content)
