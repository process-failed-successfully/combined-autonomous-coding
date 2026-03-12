from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, Input, RadioSet, RadioButton
from shared.string_case_lab import StringCaseManager

class CaseLabTab(Container):
    """Tab for String Case Conversions."""

    DEFAULT_CSS = """
    CaseLabTab {
        layout: vertical;
        height: 100%;
        overflow-y: auto;
    }

    .case-box {
        height: auto;
        border: solid $accent;
        padding: 1;
        margin: 1;
    }

    .case-output-label {
        margin-top: 1;
        text-style: bold;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = StringCaseManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Case Lab (String Case Converter)[/bold]", classes="welcome-text")

            with Vertical(classes="case-box"):
                yield Label("String to Convert:")
                yield Input(placeholder="Enter string (e.g., hello world, XMLHttp)", id="case-input")

                yield Label("Target Format:", classes="case-output-label")
                with RadioSet(id="case-format-radios"):
                    yield RadioButton("camelCase", id="radio-camel", value=True)
                    yield RadioButton("snake_case", id="radio-snake")
                    yield RadioButton("kebab-case", id="radio-kebab")
                    yield RadioButton("PascalCase", id="radio-pascal")
                    yield RadioButton("CONSTANT_CASE", id="radio-constant")
                    yield RadioButton("dot.case", id="radio-dot")
                    yield RadioButton("path/case", id="radio-path")

                with Horizontal():
                    yield Button("Convert", id="btn-case-convert", variant="primary")

                yield Label("Result:", classes="case-output-label")
                yield Input(id="case-output", disabled=True)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-case-convert":
            self.convert_string()

    def convert_string(self) -> None:
        input_widget = self.query_one("#case-input", Input)
        output_widget = self.query_one("#case-output", Input)
        radios = self.query_one("#case-format-radios", RadioSet)

        text = input_widget.value.strip()

        if not text:
            output_widget.value = ""
            return

        active_radio = radios.pressed_button
        if not active_radio:
            return

        radio_id = active_radio.id
        result = ""

        if radio_id == "radio-camel":
            result = self.manager.to_camel(text)
        elif radio_id == "radio-snake":
            result = self.manager.to_snake(text)
        elif radio_id == "radio-kebab":
            result = self.manager.to_kebab(text)
        elif radio_id == "radio-pascal":
            result = self.manager.to_pascal(text)
        elif radio_id == "radio-constant":
            result = self.manager.to_constant(text)
        elif radio_id == "radio-dot":
            result = self.manager.to_dot(text)
        elif radio_id == "radio-path":
            result = self.manager.to_path(text)

        output_widget.value = result
