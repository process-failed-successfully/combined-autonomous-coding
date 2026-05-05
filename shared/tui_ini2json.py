from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, TextArea, Label
from textual import on
from shared.ini2json_lab import Ini2JsonManager

class Ini2JsonLabTab(Container):
    """Tab for INI to JSON conversions."""

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]INI to JSON Lab[/bold]", classes="welcome-text")

            with Horizontal(classes="editor-container"):
                with Vertical(classes="editor-pane"):
                    yield Label("Input INI")
                    self.ini_input = TextArea(language="ini", id="ini-input")
                    yield self.ini_input

                with Vertical(classes="editor-pane"):
                    yield Label("Output JSON")
                    self.json_output = TextArea(language="json", id="json-output", read_only=True)
                    yield self.json_output

            with Horizontal(classes="button-row"):
                yield Button("Convert", id="btn-convert", variant="primary")
                yield Button("Clear", id="btn-clear", variant="error")
                yield Button("Copy Output", id="btn-copy", variant="success")

    @on(Button.Pressed, "#btn-convert")
    def convert_ini(self) -> None:
        ini_text = self.ini_input.text
        if not ini_text.strip():
            self.notify("Input INI is empty", severity="error")
            return

        manager = Ini2JsonManager()
        try:
            json_text = manager.convert(ini_text)
            self.json_output.text = json_text
            self.notify("Successfully converted INI to JSON")
        except Exception as e:
            self.json_output.text = f"Error: {e}"
            self.notify(f"Conversion failed: {e}", severity="error")

    @on(Button.Pressed, "#btn-clear")
    def clear_text(self) -> None:
        self.ini_input.text = ""
        self.json_output.text = ""
        self.ini_input.focus()

    @on(Button.Pressed, "#btn-copy")
    def copy_output(self) -> None:
        import pyperclip
        if self.json_output.text:
            try:
                pyperclip.copy(self.json_output.text)
                self.notify("Copied to clipboard!")
            except Exception as e:
                self.notify(f"Clipboard failed: {e}", severity="error")
        else:
            self.notify("Nothing to copy", severity="warning")
