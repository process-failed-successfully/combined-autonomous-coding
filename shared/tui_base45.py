from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Label, Input, Button, RadioSet, RadioButton, Static
from textual import on
from shared.base45_lab import base45_encode, base45_decode

class Base45LabTab(Container):
    """
    Interactive Base45 Editor Tab.
    """
    def compose(self) -> ComposeResult:
        with Vertical(classes="stat-box"):
            yield Label("[bold]Base45 Lab[/bold]")
            yield Label("Encode or decode Base45 strings interactively.")

            with Horizontal():
                with RadioSet(id="base45-mode", classes="w-1-4"):
                    yield RadioButton("Encode", value=True, id="mode-encode")
                    yield RadioButton("Decode", id="mode-decode")

            yield Label("Input:")
            yield Input(placeholder="Enter text to encode/decode...", id="base45-input")

            with Horizontal():
                yield Button("Process", id="btn-base45-process", variant="primary")
                yield Button("Clear", id="btn-base45-clear", variant="warning")

            yield Label("[bold]Output:[/bold]")
            yield Static(id="base45-output", classes="stat-box", markup=False)
            yield Static("", id="base45-error", classes="error-text")


    @on(Button.Pressed, "#btn-base45-process")
    def on_process(self) -> None:
        self.process_input()

    @on(Input.Submitted, "#base45-input")
    def on_input_submitted(self) -> None:
        self.process_input()

    def process_input(self) -> None:
        input_widget = self.query_one("#base45-input", Input)
        output_widget = self.query_one("#base45-output", Static)
        error_widget = self.query_one("#base45-error", Static)
        mode_set = self.query_one("#base45-mode", RadioSet)

        text = input_widget.value
        error_widget.update("")

        if not text:
            output_widget.update("")
            return

        try:
            if mode_set.pressed_button and mode_set.pressed_button.id == "mode-encode":
                # Encode mode
                result = base45_encode(text.encode('utf-8'))
                output_widget.update(result)
            else:
                # Decode mode
                decoded_bytes = base45_decode(text)
                try:
                    result = decoded_bytes.decode('utf-8')
                except UnicodeDecodeError:
                    result = repr(decoded_bytes)
                output_widget.update(result)
        except Exception as e:
            output_widget.update("")
            error_widget.update(f"Error: {str(e)}")

    @on(Button.Pressed, "#btn-base45-clear")
    def on_clear(self) -> None:
        self.query_one("#base45-input", Input).value = ""
        self.query_one("#base45-output", Static).update("")
        self.query_one("#base45-error", Static).update("")
        self.query_one("#base45-input", Input).focus()

    @on(RadioSet.Changed, "#base45-mode")
    def on_mode_changed(self) -> None:
        input_widget = self.query_one("#base45-input", Input)
        input_widget.focus()
        self.process_input()
