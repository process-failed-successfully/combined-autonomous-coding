from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Label, Input, Button, RadioSet, RadioButton, Static
from textual import on
from shared.punycode_lab import punycode_encode, punycode_decode


class PunycodeLabTab(Container):
    """
    Interactive Punycode (IDN) Editor Tab.
    """
    def compose(self) -> ComposeResult:
        with Vertical(classes="stat-box"):
            yield Label("[bold]Punycode Lab[/bold]")
            yield Label("Encode or decode Internationalized Domain Names (IDN/Punycode) interactively.")

            with Horizontal():
                with RadioSet(id="punycode-mode", classes="w-1-4"):
                    yield RadioButton("Encode", value=True, id="mode-encode")
                    yield RadioButton("Decode", id="mode-decode")

            yield Label("Input Domain:")
            yield Input(placeholder="Enter domain (e.g., münchen.de or xn--mnchen-3ya.de)", id="punycode-input")

            with Horizontal():
                yield Button("Process", id="btn-punycode-process", variant="primary")
                yield Button("Clear", id="btn-punycode-clear", variant="warning")

            yield Label("[bold]Output:[/bold]")
            yield Static(id="punycode-output", classes="stat-box", markup=False)
            yield Static("", id="punycode-error", classes="error-text")

    @on(Button.Pressed, "#btn-punycode-process")
    def on_process(self) -> None:
        self.process_input()

    @on(Input.Submitted, "#punycode-input")
    def on_input_submitted(self) -> None:
        self.process_input()

    def process_input(self) -> None:
        input_widget = self.query_one("#punycode-input", Input)
        output_widget = self.query_one("#punycode-output", Static)
        error_widget = self.query_one("#punycode-error", Static)
        mode_set = self.query_one("#punycode-mode", RadioSet)

        text = input_widget.value.strip()
        error_widget.update("")

        if not text:
            output_widget.update("")
            return

        try:
            if mode_set.pressed_button and mode_set.pressed_button.id == "mode-encode":
                # Encode mode
                result = punycode_encode(text)
                output_widget.update(result)
            else:
                # Decode mode
                result = punycode_decode(text)
                output_widget.update(result)
        except Exception as e:
            output_widget.update("")
            error_widget.update(f"Error: {str(e)}")

    @on(Button.Pressed, "#btn-punycode-clear")
    def on_clear(self) -> None:
        self.query_one("#punycode-input", Input).value = ""
        self.query_one("#punycode-output", Static).update("")
        self.query_one("#punycode-error", Static).update("")
        self.query_one("#punycode-input", Input).focus()

    @on(RadioSet.Changed, "#punycode-mode")
    def on_mode_changed(self) -> None:
        input_widget = self.query_one("#punycode-input", Input)
        input_widget.focus()
        self.process_input()
