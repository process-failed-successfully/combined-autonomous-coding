from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Input, Button, Label, TextArea, RichLog
from textual import work
from shared.awk_lab import AwkLabManager
from textual.widget import Widget

class AwkLabTab(Widget):
    """TUI tab for the AWK Lab."""

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("AWK Lab - Evaluate AWK Scripts", classes="tab-title"),
            Horizontal(
                Vertical(
                    Label("Text Input:"),
                    TextArea(id="awk-input-text", classes="tall-input"),
                    classes="half-width"
                ),
                Vertical(
                    Label("AWK Script:"),
                    TextArea(id="awk-script-input", classes="tall-input"),
                    classes="half-width"
                ),
                classes="input-row"
            ),
            Horizontal(
                Button("Evaluate", id="btn-awk-eval", variant="primary"),
                Button("Clear", id="btn-awk-clear"),
                classes="button-row"
            ),
            Label("Result:"),
            RichLog(id="awk-result", classes="result-log", highlight=True, markup=True)
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-awk-eval":
            self.evaluate_awk()
        elif event.button.id == "btn-awk-clear":
            self.query_one("#awk-input-text", TextArea).text = ""
            self.query_one("#awk-script-input", TextArea).text = ""
            self.query_one("#awk-result", RichLog).clear()

    @work(exclusive=True, thread=True)
    def evaluate_awk(self) -> None:
        """Evaluates the AWK script asynchronously."""
        input_text = self.query_one("#awk-input-text", TextArea).text
        script = self.query_one("#awk-script-input", TextArea).text
        result_log = self.query_one("#awk-result", RichLog)

        self.app.call_from_thread(result_log.clear)

        if not script.strip():
            self.app.call_from_thread(result_log.write, "[red]Error: Please provide an AWK script.[/red]")
            return

        manager = AwkLabManager()
        result = manager.evaluate(input_text, script)

        if result["success"]:
            # Need to safely format text for RichLog which expects markup
            # if we just print result["result"], it might interpret tags.
            # Using Text object or escaping would be safer, but write handles plain strings ok if markup=False
            # Wait, we set markup=True. So we should escape it.
            from rich.markup import escape
            safe_text = escape(result["result"])
            self.app.call_from_thread(result_log.write, safe_text)
        else:
            self.app.call_from_thread(result_log.write, f"[red]Error:[/red] {result['error']}")
