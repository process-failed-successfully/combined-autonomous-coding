from textual.widgets import TabPane, TextArea, Select, Button, Label, Markdown
from textual.containers import Vertical, Horizontal
from textual import on
from shared.props_lab import PropsLabManager
import traceback

class PropsLabTab(TabPane):
    """TUI Tab for Props Lab."""

    def __init__(self, id="tab-props", title="Props Lab"):
        super().__init__(title, id=id)
        self.manager = PropsLabManager()

    def compose(self):
        with Vertical(classes="p-4"):
            yield Markdown("## Props Lab")
            yield Markdown("Convert between Java `.properties` and JSON/YAML formats.")
            with Horizontal(classes="mb-4"):
                yield Label("Operation: ", classes="mt-2")
                yield Select(
                    [
                        ("Props to JSON", "props2json"),
                        ("JSON to Props", "json2props"),
                        ("Props to YAML", "props2yaml"),
                        ("YAML to Props", "yaml2props"),
                    ],
                    id="operation-select",
                    value="props2json",
                    classes="w-1-3"
                )

            with Horizontal(classes="flex-1 min-h-0"):
                with Vertical(classes="w-1-2 pr-2"):
                    yield Label("Input")
                    yield TextArea(id="props-input", classes="flex-1")
                with Vertical(classes="w-1-2 pl-2"):
                    yield Label("Output")
                    yield TextArea(id="props-output", classes="flex-1", read_only=True)

            with Horizontal(classes="mt-4 justify-end"):
                yield Label("", id="props-status", classes="mr-4 mt-2 text-error")
                yield Button("Convert", id="btn-convert", variant="primary")

    @on(Button.Pressed, "#btn-convert")
    def on_convert(self):
        input_widget = self.query_one("#props-input", TextArea)
        output_widget = self.query_one("#props-output", TextArea)
        status_widget = self.query_one("#props-status", Label)
        operation_widget = self.query_one("#operation-select", Select)

        input_text = input_widget.text
        operation = operation_widget.value

        if not input_text.strip():
            status_widget.update("Input is empty.")
            return

        status_widget.update("")

        try:
            if operation == "props2json":
                result = self.manager.props2json(input_text)
                output_widget.language = "json"
            elif operation == "json2props":
                result = self.manager.json2props(input_text)
                output_widget.language = "properties"
            elif operation == "props2yaml":
                result = self.manager.props2yaml(input_text)
                output_widget.language = "yaml"
            elif operation == "yaml2props":
                result = self.manager.yaml2props(input_text)
                output_widget.language = "properties"
            else:
                result = "Unknown operation."

            output_widget.text = result
        except Exception as e:
            status_widget.update(f"Error: {e}")
            output_widget.text = ""
