from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Input, Button, Label, TextArea, RichLog
from textual import work
from shared.sed_lab import SedLabManager
from textual.widget import Widget

class SedLabTab(Widget):
    """TUI tab for the SED Lab."""

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("SED Lab - Evaluate SED Scripts", classes="tab-title"),
            Horizontal(
                Vertical(
                    Label("Text Input:"),
                    TextArea(id="sed-input-text", classes="tall-input"),
                    classes="half-width"
                ),
                Vertical(
                    Label("SED Script:"),
                    TextArea(id="sed-script-input", classes="tall-input"),
                    classes="half-width"
                ),
                classes="input-row"
            ),
            Horizontal(
                Button("Evaluate", id="btn-sed-eval", variant="primary"),
                Button("Clear", id="btn-sed-clear"),
                classes="button-row"
            ),
            Label("Result:"),
            RichLog(id="sed-result", classes="result-log", highlight=True, markup=True)
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-sed-eval":
            self.evaluate_sed()
        elif event.button.id == "btn-sed-clear":
            self.query_one("#sed-input-text", TextArea).text = ""
            self.query_one("#sed-script-input", TextArea).text = ""
            self.query_one("#sed-result", RichLog).clear()

    @work(exclusive=True, thread=True)
    def evaluate_sed(self) -> None:
        """Evaluates the SED script asynchronously."""
        input_text = self.query_one("#sed-input-text", TextArea).text
        script = self.query_one("#sed-script-input", TextArea).text
        result_log = self.query_one("#sed-result", RichLog)

        self.app.call_from_thread(result_log.clear)

        if not script.strip():
            self.app.call_from_thread(result_log.write, "[red]Error: Please provide a SED script.[/red]")
            return

        manager = SedLabManager()
        result = manager.evaluate(input_text, script)

        if result["success"]:
            from rich.markup import escape
            safe_text = escape(result["result"])
            self.app.call_from_thread(result_log.write, safe_text)
        else:
            safe_err = escape(result['error'])
            self.app.call_from_thread(result_log.write, f"[red]Error:[/red] {safe_err}")
