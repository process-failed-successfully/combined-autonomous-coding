from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Input, Button, Static, TextArea
import json

from shared.xpath_lab import XpathLabManager


class XpathLabTab(Container):
    """TUI Tab for XPath Lab."""

    def __init__(self, project_dir: Path | None = None):
        super().__init__()
        self.project_dir = project_dir
        self.manager = XpathLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("XPath Lab", classes="tab-title")
            yield Static("Evaluate XPath expressions against XML data.", classes="tab-subtitle")

            with Horizontal(classes="input-row"):
                self.expression_input = Input(placeholder="XPath expression (e.g., .//book)", id="xpath-expression")
                yield self.expression_input
                yield Button("Evaluate", id="btn-evaluate", variant="primary")
                yield Button("Clear", id="btn-clear")

            with Horizontal(classes="editor-row"):
                with Vertical(classes="editor-pane"):
                    yield Static("Input XML:")
                    self.input_area = TextArea(id="xpath-input")
                    try:
                        self.input_area.language = "xml"
                    except Exception:
                        pass
                    yield self.input_area
                with Vertical(classes="editor-pane"):
                    yield Static("Result:")
                    self.result_area = TextArea(language="json", id="xpath-result", read_only=True)
                    yield self.result_area

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-evaluate":
            self.action_evaluate()
        elif event.button.id == "btn-clear":
            self.expression_input.value = ""
            self.input_area.text = ""
            self.result_area.text = ""

    def action_evaluate(self) -> None:
        xml_data = self.input_area.text.strip()
        expression = self.expression_input.value.strip()

        if not xml_data:
            self.result_area.text = '{"error": "Empty XML input"}'
            return

        if not expression:
            self.result_area.text = '{"error": "Empty XPath expression"}'
            return

        result = self.manager.evaluate(xml_data, expression)
        if result["success"]:
            self.result_area.text = json.dumps(result["result"], indent=2)
        else:
            self.result_area.text = json.dumps({"error": result["error"]}, indent=2)
