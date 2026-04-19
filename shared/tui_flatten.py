import json
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, TextArea, Static, TabPane
from shared.flatten_lab import FlattenManager

class FlattenLabTab(TabPane):
    """Interactive TUI for JSON Flattening and Unflattening."""

    def __init__(self, *args, **kwargs):
        super().__init__("JSON Flatten Lab", id="tab-flatten", *args, **kwargs)
        self.manager = FlattenManager()

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical(classes="column"):
                yield Static("Nested JSON:", classes="header-label")
                yield TextArea(
                    "{\n  \"user\": {\n    \"name\": \"Alice\",\n    \"roles\": [\"admin\", \"user\"]\n  }\n}",
                    id="nested-json",
                    language="json",
                )

            with Vertical(classes="button-column", id="flatten-buttons"):
                yield Button("Flatten ->", id="btn-flatten", variant="primary")
                yield Button("<- Unflatten", id="btn-unflatten", variant="success")

            with Vertical(classes="column"):
                yield Static("Flattened JSON (dot-separated):", classes="header-label")
                yield TextArea(id="flat-json", language="json")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        nested_ta = self.query_one("#nested-json", TextArea)
        flat_ta = self.query_one("#flat-json", TextArea)

        if event.button.id == "btn-flatten":
            text = nested_ta.text.strip()
            if not text:
                self.notify("Please enter nested JSON to flatten.", severity="warning")
                return

            try:
                data = json.loads(text)
                flat_data = self.manager.flatten(data)
                flat_ta.text = json.dumps(flat_data, indent=2)
                self.notify("JSON successfully flattened.", severity="information")
            except json.JSONDecodeError as e:
                self.notify(f"Invalid JSON: {e}", severity="error")
            except Exception as e:
                self.notify(f"Error flattening JSON: {e}", severity="error")

        elif event.button.id == "btn-unflatten":
            text = flat_ta.text.strip()
            if not text:
                self.notify("Please enter flattened JSON to unflatten.", severity="warning")
                return

            try:
                data = json.loads(text)
                if not isinstance(data, dict):
                    self.notify("Flattened JSON must be an object (dictionary).", severity="error")
                    return

                nested_data = self.manager.unflatten(data)
                nested_ta.text = json.dumps(nested_data, indent=2)
                self.notify("JSON successfully unflattened.", severity="information")
            except json.JSONDecodeError as e:
                self.notify(f"Invalid JSON: {e}", severity="error")
            except Exception as e:
                self.notify(f"Error unflattening JSON: {e}", severity="error")
