from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, TextArea, Input

from shared.json2ts_lab import Json2TsManager

class Json2TsTab(Container):
    """Tab for JSON to TypeScript Lab."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = Json2TsManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]JSON to TypeScript Converter[/bold]", classes="welcome-text")

            with Horizontal(classes="stat-box"):
                yield Label("Root Interface Name: ", classes="label")
                yield Input(placeholder="Root", id="root-name-input", value="Root")

            with Horizontal():
                with Vertical(classes="stat-box"):
                    yield Label("[bold]Input (JSON)[/bold]")
                    yield TextArea(id="json2ts-input", language="json")
                with Vertical(classes="stat-box"):
                    yield Label("[bold]Output (TypeScript)[/bold]")
                    yield TextArea(id="json2ts-output", language="typescript", read_only=True)

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "root-name-input":
            self._update_output()

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        if event.text_area.id == "json2ts-input":
            self._update_output()

    def _update_output(self) -> None:
        input_area = self.query_one("#json2ts-input", TextArea)
        output_area = self.query_one("#json2ts-output", TextArea)
        root_name = self.query_one("#root-name-input", Input).value or "Root"

        content = input_area.text
        if not content.strip():
            output_area.text = ""
            return

        ts_output = self.manager.convert(content, root_name=root_name)
        output_area.text = ts_output
