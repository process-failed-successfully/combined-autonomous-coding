import json
from textual.app import ComposeResult
from textual.widgets import TabPane, TextArea, Button, RichLog
from textual.containers import Vertical
from textual import on
from shared.syslog_lab import SyslogLabManager

class SyslogLabTab(TabPane):
    """Tab for experimenting with Syslog messages."""
    def __init__(self, **kwargs):
        super().__init__("Syslog Lab", id="tab-syslog", **kwargs)
        self.manager = SyslogLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield TextArea(id="syslog-input", placeholder="Paste a syslog message here...\ne.g. <34>1 2003-10-11T22:14:15.003Z mymachine.example.com su - ID47 - 'su root' failed for lonvick on /dev/pts/8")
            yield Button("Parse", id="btn-syslog-parse", variant="primary")
            yield RichLog(id="syslog-output", wrap=True, highlight=True, markup=True)

    @on(Button.Pressed, "#btn-syslog-parse")
    def on_parse(self, event: Button.Pressed) -> None:
        text = self.query_one("#syslog-input", TextArea).text.strip()
        log = self.query_one("#syslog-output", RichLog)
        log.clear()

        if not text:
            log.write("[red]Please enter a syslog message[/red]")
            return

        try:
            parsed = self.manager.parse(text)
            log.write(json.dumps(parsed, indent=2))
        except Exception as e:
            from rich.markup import escape
            log.write(f"[red]Error:[/red] {escape(str(e))}")
