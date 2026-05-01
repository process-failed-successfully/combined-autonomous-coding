from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import TextArea, Button, Static, Label
from textual import work
from pathlib import Path
from shared.ini2json_lab import Ini2JsonManager


class Ini2JsonTab(Vertical):
    """A TUI tab for converting INI to JSON."""

    def __init__(self, project_dir: Path, **kwargs):
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = Ini2JsonManager(project_dir=project_dir)

    def compose(self) -> ComposeResult:
        yield Label("INI to JSON Converter", id="title-ini2json", classes="tab-title")
        yield Label("Enter INI text below:", classes="input-label")
        yield TextArea(id="input-ini-text", language="ini", classes="input-textarea")
        with Horizontal(classes="button-row"):
            yield Button("Convert to JSON", id="btn-convert-ini2json", variant="primary")
            yield Button("Clear", id="btn-clear-ini2json", variant="error")
        yield Label("JSON Output:", classes="output-label")
        yield TextArea(id="output-json-text", language="json", read_only=True, classes="output-textarea")
        yield Static(id="status-ini2json", classes="status-message")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-convert-ini2json":
            self.convert_action()
        elif event.button.id == "btn-clear-ini2json":
            self.clear_action()

    @work(exclusive=True)
    async def convert_action(self) -> None:
        """Runs the conversion logic."""
        input_widget = self.query_one("#input-ini-text", TextArea)
        output_widget = self.query_one("#output-json-text", TextArea)
        status_widget = self.query_one("#status-ini2json", Static)

        ini_data = input_widget.text

        if not ini_data.strip():
            self.app.call_from_thread(status_widget.update, "Please enter some INI text to convert.")
            return

        try:
            # We call the synchronous convert function inside the worker thread
            json_str = self.manager.convert(ini_data)
            self.app.call_from_thread(output_widget.load_text, json_str)
            self.app.call_from_thread(status_widget.update, "[green]Successfully converted INI to JSON![/green]")
        except Exception as e:
            self.app.call_from_thread(status_widget.update, f"[red]Error during conversion: {e}[/red]")
            self.app.call_from_thread(output_widget.load_text, "")

    def clear_action(self) -> None:
        """Clears the text areas."""
        input_widget = self.query_one("#input-ini-text", TextArea)
        output_widget = self.query_one("#output-json-text", TextArea)
        status_widget = self.query_one("#status-ini2json", Static)

        input_widget.load_text("")
        output_widget.load_text("")
        status_widget.update("")
