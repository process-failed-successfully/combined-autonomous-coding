from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Label, Button, TextArea
from textual.containers import ScrollableContainer

from shared.props_lab import PropsLabManager

class PropsLabTab(ScrollableContainer):
    """TUI Tab for Properties Converter Lab."""

    def __init__(self, project_dir=None, **kwargs):
        super().__init__(**kwargs)
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        with Vertical(classes="tab-content"):
            yield Label("[bold]Properties Converter Lab[/bold] - Convert .properties <-> JSON/YAML", classes="tab-title")

            with Horizontal(classes="action-bar"):
                yield Button("Props -> JSON", id="btn-props2json", variant="primary")
                yield Button("Props -> YAML", id="btn-props2yaml", variant="primary")
                yield Button("JSON -> Props", id="btn-json2props", variant="success")
                yield Button("YAML -> Props", id="btn-yaml2props", variant="success")
                yield Button("Clear", id="btn-props-clear", variant="warning")

            with Horizontal():
                with Vertical(classes="panel"):
                    yield Label("Java Properties (.properties):")
                    yield TextArea(id="props-text", language="properties")

                with Vertical(classes="panel"):
                    yield Label("JSON:")
                    yield TextArea(id="json-text", language="json")

                with Vertical(classes="panel"):
                    yield Label("YAML:")
                    yield TextArea(id="yaml-text", language="yaml")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-props2json":
            self.props_to_json()
        elif event.button.id == "btn-props2yaml":
            self.props_to_yaml()
        elif event.button.id == "btn-json2props":
            self.json_to_props()
        elif event.button.id == "btn-yaml2props":
            self.yaml_to_props()
        elif event.button.id == "btn-props-clear":
            self.clear_all()

    def props_to_json(self) -> None:
        props_area = self.query_one("#props-text", TextArea)
        json_area = self.query_one("#json-text", TextArea)
        props_str = props_area.text.strip()

        if not props_str:
            self.app.notify("Properties input is required.", severity="error")
            return

        try:
            json_str = PropsLabManager.props_to_json(props_str)
            json_area.text = json_str
            self.app.notify("Converted Properties to JSON.")
        except Exception as e:
            self.app.notify(f"Conversion Error: {e}", severity="error")

    def props_to_yaml(self) -> None:
        props_area = self.query_one("#props-text", TextArea)
        yaml_area = self.query_one("#yaml-text", TextArea)
        props_str = props_area.text.strip()

        if not props_str:
            self.app.notify("Properties input is required.", severity="error")
            return

        try:
            yaml_str = PropsLabManager.props_to_yaml(props_str)
            yaml_area.text = yaml_str
            self.app.notify("Converted Properties to YAML.")
        except Exception as e:
            self.app.notify(f"Conversion Error: {e}", severity="error")

    def json_to_props(self) -> None:
        json_area = self.query_one("#json-text", TextArea)
        props_area = self.query_one("#props-text", TextArea)
        json_str = json_area.text.strip()

        if not json_str:
            self.app.notify("JSON input is required.", severity="error")
            return

        try:
            props_str = PropsLabManager.json_to_props(json_str)
            props_area.text = props_str
            self.app.notify("Converted JSON to Properties.")
        except Exception as e:
            self.app.notify(f"Conversion Error: {e}", severity="error")

    def yaml_to_props(self) -> None:
        yaml_area = self.query_one("#yaml-text", TextArea)
        props_area = self.query_one("#props-text", TextArea)
        yaml_str = yaml_area.text.strip()

        if not yaml_str:
            self.app.notify("YAML input is required.", severity="error")
            return

        try:
            props_str = PropsLabManager.yaml_to_props(yaml_str)
            props_area.text = props_str
            self.app.notify("Converted YAML to Properties.")
        except Exception as e:
            self.app.notify(f"Conversion Error: {e}", severity="error")

    def clear_all(self) -> None:
        self.query_one("#props-text", TextArea).text = ""
        self.query_one("#json-text", TextArea).text = ""
        self.query_one("#yaml-text", TextArea).text = ""
        self.app.notify("Fields cleared.")
