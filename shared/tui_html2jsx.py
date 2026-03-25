from textual.app import ComposeResult
from textual.widgets import Label, Button, TextArea, Switch, Input
from textual.containers import Container, Horizontal, Vertical
from textual import on
from shared.html2jsx_lab import Html2JsxManager
import traceback


class Html2JsxLabTab(Container):
    """
    Tab for HTML to JSX Lab operations.
    """
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = Html2JsxManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]HTML to JSX Lab[/bold]", classes="welcome-text")

            with Horizontal(classes="stat-box"):
                yield Button("Convert to JSX", id="btn-convert", variant="primary")
                yield Button("Clear", id="btn-clear", variant="error")

                with Horizontal(id="component-options", classes="p-1"):
                    yield Switch(value=False, id="switch-component")
                    yield Label("Wrap in Component", classes="pt-1 pr-2")
                    yield Input(placeholder="MyComponent", id="input-component-name", value="MyComponent")

            with Horizontal():
                with Vertical(classes="stat-box w-1-2"):
                    yield Label("HTML Input:")
                    yield TextArea(id="html-input", language="html")

                with Vertical(classes="stat-box w-1-2"):
                    yield Label("JSX Output:")
                    yield TextArea(id="jsx-output", read_only=True, language="javascript")

    @on(Button.Pressed, "#btn-convert")
    def on_convert(self) -> None:
        html_input = self.query_one("#html-input", TextArea).text
        output_area = self.query_one("#jsx-output", TextArea)

        if not html_input.strip():
            self.notify("Input HTML is required.", severity="error")
            return

        create_component = self.query_one("#switch-component", Switch).value
        component_name = self.query_one("#input-component-name", Input).value.strip() or "MyComponent"

        try:
            jsx = self.manager.convert(html_input, create_component, component_name)
            output_area.text = jsx
            self.notify("Conversion complete.")
        except Exception as e:
            output_area.text = f"Error during conversion:\n{e}\n\n{traceback.format_exc()}"
            self.notify("Conversion failed.", severity="error")

    @on(Button.Pressed, "#btn-clear")
    def on_clear(self) -> None:
        self.query_one("#html-input", TextArea).text = ""
        self.query_one("#jsx-output", TextArea).text = ""

    @on(Switch.Changed, "#switch-component")
    def on_switch_changed(self, event: Switch.Changed) -> None:
        pass  # Automatically handles toggling state
