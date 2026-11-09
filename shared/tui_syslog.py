import json
from textual.app import ComposeResult
from textual.widgets import Label, Button, Input, RichLog, TabbedContent, TabPane, Static
from textual.containers import Vertical, Horizontal
from textual import on
from shared.syslog_lab import SyslogLabManager

class SyslogLabTab(TabPane):
    """Tab for Syslog Lab (Parsing RFC 3164 and RFC 5424)."""

    def __init__(self, **kwargs) -> None:
        super().__init__("Syslog Lab", id="tab-syslog-lab", **kwargs)
        self.manager = SyslogLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Syslog Lab[/bold]", classes="welcome-text")

            with Vertical(classes="stat-box"):
                yield Label("[bold]Parse Syslog Message[/bold]")

                yield Label("Raw Syslog Message:")
                yield Input(placeholder="<165>1 2003-10-11T22:14:15.003Z ...", id="input-syslog-raw")

                yield Button("Parse", id="btn-syslog-parse", variant="primary")

                yield Label("[bold]Parsed Result:[/bold]")
                yield RichLog(id="log-syslog-parsed", wrap=True, highlight=True, markup=True)

    @on(Button.Pressed, "#btn-syslog-parse")
    def action_parse_syslog(self) -> None:
        """Parses the input syslog message."""
        log = self.query_one("#log-syslog-parsed", RichLog)
        raw_msg = self.query_one("#input-syslog-raw", Input).value.strip()

        if not raw_msg:
            log.write("[red]Error: Syslog message cannot be empty.[/red]")
            return

        try:
            parsed = self.manager.parse(raw_msg)
            # Pretty-print the dictionary to the log
            from rich.markup import escape
            log.write(escape(json.dumps(parsed, indent=2)))
        except Exception as e:
            from rich.markup import escape
            log.write(f"[red]Error parsing syslog message:[/red] {escape(str(e))}")
