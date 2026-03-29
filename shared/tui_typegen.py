from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Label, Button, Input, Select, TextArea, RichLog
from textual import on
from pathlib import Path

from shared.typegen_lab import TypegenManager






class TypegenLabTab(Container):
    """Tab for Typegen Lab operations."""

    def __init__(self, project_dir: Path = Path("."), *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project_dir = project_dir
        self.manager = TypegenManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Typegen Lab[/bold]", classes="welcome-text")

            with Horizontal(classes="action-buttons"):
                yield Button("Generate", id="btn-typegen-generate", variant="primary")
                yield Button("Clear", id="btn-typegen-clear", variant="error")

            with Horizontal(classes="config-row"):
                yield Label("Root Struct Name:")
                yield Input(value="Root", id="typegen-root-name")

                yield Label("Language:")
                yield Select.from_values(
                    ["typescript", "go", "python", "rust"],
                    id="typegen-lang", value="typescript"
                )

            with Horizontal(classes="editor-row"):
                with Vertical():
                    yield Label("JSON Input:")
                    yield TextArea(
                        language="json",
                        id="typegen-json-input",
                        text='{\n  "id": 1,\n  "name": "Test",\n  "active": true\n}'
                    )

                with Vertical():
                    yield Label("Generated Types:")
                    yield TextArea(
                        id="typegen-output",
                        read_only=True
                    )

            yield RichLog(id="typegen-log", markup=True, wrap=True, highlight=False, classes="typegen-log")

    @on(Button.Pressed, "#btn-typegen-generate")
    def on_generate(self) -> None:
        json_input = self.query_one("#typegen-json-input", TextArea).text
        output = self.query_one("#typegen-output", TextArea)
        log = self.query_one("#typegen-log", RichLog)

        root_name = self.query_one("#typegen-root-name", Input).value or "Root"
        lang = self.query_one("#typegen-lang", Select).value or "typescript"

        log.clear()

        if not json_input.strip():
            log.write("[bold red]Error: No JSON input provided[/bold red]")
            return

        try:
            result = self.manager.generate(json_input, root_name=root_name, lang=lang)
            if "Error parsing JSON" in result or "must be an object or array" in result:
                log.write(f"[bold red]{result}[/bold red]")
                output.text = ""
                return

            prefix = ""
            if lang == "python":
                prefix = "from dataclasses import dataclass\nfrom typing import Any, List\n\n"
            elif lang == "rust":
                prefix = "use serde::{Serialize, Deserialize};\n\n"

            output.text = prefix + result
            output.language = lang if lang in ["typescript", "go", "python", "rust"] else None
            log.write("[bold green]✅ Types generated successfully[/bold green]")
        except Exception as e:
            log.write(f"[bold red]Unexpected Error: {e}[/bold red]")

    @on(Button.Pressed, "#btn-typegen-clear")
    def on_clear(self) -> None:
        self.query_one("#typegen-json-input", TextArea).text = ""
        self.query_one("#typegen-output", TextArea).text = ""
        self.query_one("#typegen-log", RichLog).clear()
