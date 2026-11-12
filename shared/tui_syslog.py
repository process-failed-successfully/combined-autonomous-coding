from typing import Optional
from textual.app import ComposeResult
from textual.widgets import Label, Button, Input, Static, TabPane
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual import on
import json

from shared.syslog_lab import SyslogLabManager

class SyslogLabTab(TabPane):
    """
    Interactive Syslog Lab Tab.
    """
    def __init__(self, **kwargs) -> None:
        super().__init__("Syslog Lab", id="tab-syslog", **kwargs)
        self.manager = SyslogLabManager()

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Label("[bold]Syslog Lab[/bold]", classes="welcome-text")

            with Container(classes="stat-box"):
                yield Label("Raw Syslog Message:")
                yield Input(placeholder="<34>1 2003-10-11T22:14:15.003Z mymachine.example.com su - ID47 - 'su root' failed", id="syslog-input")

                with Horizontal():
                    yield Button("Parse", id="btn-syslog-parse", variant="primary")

            with Container(classes="stat-box"):
                yield Label("[bold]Parsed Result[/bold]")
                yield Static(id="syslog-output", markup=False)

    @on(Button.Pressed, "#btn-syslog-parse")
    def on_parse(self) -> None:
        message = self.query_one("#syslog-input", Input).value
        output = self.query_one("#syslog-output", Static)

        if not message:
            output.update("Error: Message is required.")
            return

        try:
            result = self.manager.parse_syslog(message)
            output.update(json.dumps(result, indent=2))
        except Exception as e:
            output.update(f"Error parsing syslog message: {e}")
