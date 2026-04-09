from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Button, TextArea, Label
from textual.binding import Binding

from shared.yaml2xml_lab import Yaml2XmlManager

class Yaml2XmlTab(Container):
    """Tab for YAML to XML conversion."""

    BINDINGS = [
        Binding("ctrl+c", "copy_xml", "Copy XML", show=True),
        Binding("ctrl+v", "paste_yaml", "Paste YAML", show=True),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.manager = Yaml2XmlManager()

    def compose(self) -> ComposeResult:
        yield Label("[bold]YAML to XML Lab[/bold] - Convert YAML formats to XML", classes="welcome-text")

        with Horizontal(id="yaml2xml-io-container"):
            with Container(classes="io-pane"):
                yield Label("YAML Input")
                yield TextArea(
                    "user:\n  name: John Doe\n  age: 30\n  roles:\n    - admin\n    - user",
                    id="yaml2xml-input",
                    language="yaml"
                )
                with Horizontal(classes="button-row"):
                    yield Button("Convert to XML", id="btn-yaml2xml-convert", variant="primary")
                    yield Button("Clear", id="btn-yaml2xml-clear", variant="error")

            with Container(classes="io-pane"):
                yield Label("XML Output")
                # Textual's default available languages might not include 'xml', so we omit it
                # or use None / default to prevent LanguageDoesNotExist.
                yield TextArea(id="yaml2xml-output", read_only=True)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-yaml2xml-convert":
            self.action_convert()
        elif event.button.id == "btn-yaml2xml-clear":
            self.query_one("#yaml2xml-input", TextArea).text = ""
            self.query_one("#yaml2xml-output", TextArea).text = ""

    def action_convert(self) -> None:
        """Converts the YAML in the input area to XML in the output area."""
        yaml_text = self.query_one("#yaml2xml-input", TextArea).text.strip()
        output_area = self.query_one("#yaml2xml-output", TextArea)

        if not yaml_text:
            output_area.text = ""
            return

        try:
            xml_text = self.manager.convert(yaml_text, root_name="root")
            output_area.text = xml_text
        except Exception as e:
            output_area.text = f"Error converting YAML: {str(e)}"

    def action_copy_xml(self) -> None:
        """Copies the XML output to clipboard."""
        import pyperclip
        text = self.query_one("#yaml2xml-output", TextArea).text
        if text:
            try:
                pyperclip.copy(text)
                self.notify("XML copied to clipboard")
            except Exception:
                self.notify("Clipboard not available", severity="error")

    def action_paste_yaml(self) -> None:
        """Pastes YAML from clipboard."""
        import pyperclip
        try:
            text = pyperclip.paste()
            if text:
                self.query_one("#yaml2xml-input", TextArea).text = text
                self.action_convert()
        except Exception:
            self.notify("Clipboard not available", severity="error")
