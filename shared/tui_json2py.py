from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import TabPane, Label, Button, TextArea, Select, Input
from shared.json2py_lab import Json2PyManager
import pyperclip

class Json2PyLabTab(TabPane):
    """Tab pane for Json2Py Lab."""

    def __init__(self, *args, **kwargs):
        super().__init__("JSON to Py", id="tab-json2py", *args, **kwargs)
        self.manager = Json2PyManager()

    def compose(self) -> ComposeResult:
        with Vertical(classes="p-4"):
            yield Label("JSON to Python Dataclass / Pydantic", classes="text-xl text-primary mb-4")

            with Horizontal(classes="mb-4 h-auto"):
                yield Label("Root Class Name:", classes="w-32")
                yield Input(value="RootModel", id="input-json2py-root", classes="w-48 mr-4")

                yield Label("Framework:", classes="w-24")
                yield Select(
                    [("Dataclass", "dataclass"), ("Pydantic", "pydantic"), ("Msgspec", "msgspec"), ("TypedDict", "typeddict")],
                    value="dataclass",
                    id="select-json2py-framework",
                    classes="w-40 mr-4"
                )

                yield Button("Generate", variant="primary", id="btn-generate-json2py", classes="mr-4")
                yield Button("Copy Output", variant="default", id="btn-copy-json2py")

            with Horizontal():
                with Vertical(classes="w-1-2 pr-2"):
                    yield Label("Input (JSON):", classes="mb-2")
                    yield TextArea(language="json", id="editor-json2py-in")
                with Vertical(classes="w-1-2 pl-2"):
                    yield Label("Output (Python):", classes="mb-2")
                    yield TextArea(language="python", read_only=True, id="editor-json2py-out")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-generate-json2py":
            in_editor = self.query_one("#editor-json2py-in", TextArea)
            out_editor = self.query_one("#editor-json2py-out", TextArea)

            root_name = self.query_one("#input-json2py-root", Input).value or "RootModel"
            framework = self.query_one("#select-json2py-framework", Select).value or "dataclass"

            json_str = in_editor.text
            if not json_str.strip():
                if hasattr(self.app, 'notify'):
                    self.app.notify("Input JSON cannot be empty.", severity="warning")
                return

            try:
                result = self.manager.generate(json_str, framework=framework, root_name=root_name)
                out_editor.text = result
                if hasattr(self.app, 'notify'):
                    self.app.notify("Python code generated successfully.")
            except Exception as e:
                out_editor.text = f"Error generating code:\n{e}"
                if hasattr(self.app, 'notify'):
                    self.app.notify(f"Error: {e}", severity="error")

        elif event.button.id == "btn-copy-json2py":
            out_editor = self.query_one("#editor-json2py-out", TextArea)
            content = out_editor.text
            if content:
                try:
                    pyperclip.copy(content)
                    if hasattr(self.app, 'notify'):
                        self.app.notify("Copied to clipboard!", title="Success")
                except Exception as e:
                    if hasattr(self.app, 'notify'):
                        self.app.notify(f"Failed to copy: {e}", title="Error", severity="error")
