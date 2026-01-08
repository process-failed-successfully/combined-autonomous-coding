from pathlib import Path
import_path = str(Path(__file__).parent.parent)
import sys
sys.path.append(import_path)

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, RichLog
from textual.reactive import reactive
from textual.screen import Screen
from textual.containers import VerticalScroll, Horizontal, Container

from shared.cli_utils import _run_enhanced_status_logic, get_suggestions, _run_history_logic, get_latest_log_file

class Welcome(Static):
    """A welcome widget."""
    def on_mount(self) -> None:
        self.update("Welcome to the Agent TUI!\n\n"
                    "Press 'd' to toggle dark mode.\n"
                    "Press 'q' to quit.")

class ProjectStatus(Static):
    """A widget to display the project status."""

    project_dir = reactive(Path("."))

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir

    def on_mount(self) -> None:
        """Event handler called when widget is added to the app."""
        self.update_status()
        self.set_interval(5, self.update_status)

    def update_status(self) -> None:
        """Update the project status text."""
        status_text = _run_enhanced_status_logic(self.project_dir)
        self.update(status_text)

class Suggestions(Static):
    """A widget to display suggested next steps."""

    project_dir = reactive(Path("."))

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir

    def on_mount(self) -> None:
        """Event handler called when widget is added to the app."""
        self.update_suggestions()
        self.set_interval(10, self.update_suggestions)

    def update_suggestions(self) -> None:
        """Update the suggestions text."""
        suggestions = get_suggestions(self.project_dir, limit=3)
        if not suggestions:
            self.update("✅ [bold green]Project is in a clean state.[/bold green]")
            return

        lines = ["[bold]Suggested Next Steps:[/bold]"]
        for suggestion in suggestions:
            lines.append(f"👉 [yellow]{suggestion['command']}[/yellow]")
            lines.append(f"   [dim]{suggestion['reason']}[/dim]")
        self.update("\n".join(lines))

class History(Static):
    """A widget to display agent run history."""

    project_dir = reactive(Path("."))

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir

    def on_mount(self) -> None:
        """Event handler called when widget is added to the app."""
        self.update_history()
        self.set_interval(10, self.update_history)

    def update_history(self) -> None:
        """Update the history text."""
        history_text = _run_history_logic(self.project_dir)
        self.update(history_text)

class Dashboard(Screen):
    """The main dashboard screen for the TUI."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="main-container"):
            with Horizontal(id="top-pane"):
                with VerticalScroll(id="left-column"):
                    yield ProjectStatus(self.project_dir, id="project-status")
                    yield Suggestions(self.project_dir, id="suggestions")
                with VerticalScroll(id="right-column"):
                    yield History(self.project_dir, id="history")
            yield RichLog(id="log-viewer", wrap=True, highlight=True)
        yield Footer()

    def on_mount(self) -> None:
        """Event handler called when the screen is mounted."""
        self.query_one("#log-viewer", RichLog).write("Log viewer initialized...")
        self.set_interval(2, self.update_log_viewer)

    def update_log_viewer(self) -> None:
        """Callback to update the log viewer content."""
        log_file = get_latest_log_file()
        log_viewer = self.query_one("#log-viewer", RichLog)

        if log_file and log_file.exists():
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    log_viewer.clear()
                    log_viewer.write("".join(lines[-100:]))
            except Exception as e:
                log_viewer.write(f"\nError reading log file: {e}")
        else:
            log_viewer.clear()
            log_viewer.write("No log file found.")


class AgentTUI(App):
    """A Textual user interface for the autonomous coding agent."""

    CSS_PATH = "tui.css"
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir

    def on_mount(self) -> None:
        """Event handler called when the app is first mounted."""
        self.push_screen(Dashboard(self.project_dir))


if __name__ == "__main__":
    project_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    app = AgentTUI(project_dir=project_path)
    app.run()
