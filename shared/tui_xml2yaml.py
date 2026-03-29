from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, TextArea, Select, Static
from textual.reactive import reactive
from textual.binding import Binding

from shared.xml2yaml_lab import Xml2YamlManager


class Xml2YamlTab(Container):
    """A Textual tab for converting between XML and YAML."""

    BINDINGS = [
        Binding("ctrl+r", "convert", "Convert"),
        Binding("ctrl+x", "clear", "Clear Inputs"),
    ]

    mode: reactive[str] = reactive("xml2yaml")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.manager = Xml2YamlManager()

    def compose(self) -> ComposeResult:
        with Vertical(id="main_layout"):
            with Horizontal(id="toolbar", classes="toolbar"):
                yield Select(
                    [("XML to YAML", "xml2yaml"), ("YAML to XML", "yaml2xml")],
                    value="xml2yaml",
                    id="mode_select"
                )
                yield Button("Convert (Ctrl+R)", id="convert_btn", variant="primary")
                yield Button("Clear (Ctrl+X)", id="clear_btn", variant="error")

            with Horizontal(id="editors"):
                with Vertical(classes="editor_pane"):
                    yield Static("Input", classes="pane_label")
                    yield TextArea(id="input_area")

                with Vertical(classes="editor_pane"):
                    yield Static("Output", classes="pane_label")
                    yield TextArea(id="output_area", read_only=True)

            yield Static(id="status_bar")

    def on_mount(self) -> None:
        self.query_one("#input_area", TextArea).focus()
        self.update_status("Ready")

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "mode_select":
            if event.value == Select.BLANK:
                return
            self.mode = str(event.value)
            input_area = self.query_one("#input_area", TextArea)
            output_area = self.query_one("#output_area", TextArea)
            if self.mode == "xml2yaml":
                try:
                    input_area.language = "xml"
                    output_area.language = "yaml"
                except Exception:
                    pass
            else:
                try:
                    input_area.language = "yaml"
                    output_area.language = "xml"
                except Exception:
                    pass
            self.update_status(f"Mode changed to {self.mode}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "convert_btn":
            self.action_convert()
        elif event.button.id == "clear_btn":
            self.action_clear()

    def action_convert(self) -> None:
        input_text = self.query_one("#input_area", TextArea).text
        output_area = self.query_one("#output_area", TextArea)

        if not input_text.strip():
            self.update_status("Error: Input is empty.")
            return

        try:
            if self.mode == "xml2yaml":
                result = self.manager.convert_xml_to_yaml(input_text)
                self.update_status("Successfully converted XML to YAML.")
            else:
                result = self.manager.convert_yaml_to_xml(input_text)
                self.update_status("Successfully converted YAML to XML.")

            output_area.text = result
        except Exception as e:
            self.update_status(f"Error: {e}")
            output_area.text = ""

    def action_clear(self) -> None:
        self.query_one("#input_area", TextArea).text = ""
        self.query_one("#output_area", TextArea).text = ""
        self.update_status("Cleared all fields.")
        self.query_one("#input_area", TextArea).focus()

    def update_status(self, message: str) -> None:
        status_bar = self.query_one("#status_bar", Static)
        status_bar.update(message)
