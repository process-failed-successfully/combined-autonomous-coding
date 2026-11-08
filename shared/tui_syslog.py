from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Button, Static, TabPane, TextArea, RichLog
from textual import work
import json

from shared.syslog_lab import SyslogLabManager

class SyslogLabTab(TabPane):
    """TUI Tab for Syslog Lab."""

    def __init__(self):
        super().__init__("Syslog Lab", id="tab-syslog")
        self.manager = SyslogLabManager()

    def compose(self) -> ComposeResult:
        with Vertical(classes="p-4"):
            yield Static("Syslog Parser (RFC 3164 & RFC 5424)", classes="text-xl text-bold mb-4")

            with Vertical(classes="mb-4 h-auto"):
                yield Static("Enter Syslog Message:", classes="mb-2")
                yield TextArea(id="syslog-input", language="text")

            with Horizontal(classes="mb-4 h-auto"):
                yield Button("Parse", id="btn-syslog-parse", variant="primary")

            yield Static("Parsed Output:", classes="mt-4 mb-2")
            yield RichLog(id="syslog-output", wrap=True, highlight=True, markup=True)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-syslog-parse":
            self.action_parse()

    @work(exclusive=True, thread=True)
    def action_parse(self) -> None:
        input_widget = self.query_one("#syslog-input", TextArea)
        output_log = self.query_one("#syslog-output", RichLog)

        syslog_text = input_widget.text.strip()
        if not syslog_text:
            self.app.call_from_thread(output_log.clear)
            self.app.call_from_thread(output_log.write, "[red]Error: Please enter a syslog message.[/red]")
            return

        self.app.call_from_thread(output_log.clear)
        self.app.call_from_thread(output_log.write, "Parsing...")

        lines = [line for line in syslog_text.splitlines() if line.strip()]
        results = []
        for line in lines:
            results.append(self.manager.parse(line))

        if len(results) == 1:
            res = results[0]
            if "error" in res:
                formatted = f"[red]Error:[/red] {res['error']}"
            else:
                formatted = json.dumps(res, indent=2)
        else:
            formatted = json.dumps(results, indent=2)

        self.app.call_from_thread(output_log.clear)
        self.app.call_from_thread(output_log.write, formatted)
