import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Log
from textual.containers import Container
from shared.cli_utils import _run_summary_logic


class TUI(App):
    """A Textual interface for the autonomous coding agent."""

    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()
        with Container(id="app-grid"):
            with Container(id="left-pane"):
                yield Static(id="summary")
            with Container(id="right-pane"):
                yield Log(id="log")

    def on_mount(self) -> None:
        """Called when the app is mounted."""
        log = self.query_one(Log)
        log.write_line("TUI started. Welcome!")

        summary_widget = self.query_one("#summary")
        summary_text = _run_summary_logic(Path("."))
        summary_widget.update(summary_text)

if __name__ == "__main__":
    app = TUI()
    app.run()
