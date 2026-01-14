from pathlib import Path
import_path = str(Path(__file__).parent.parent)
import sys
sys.path.append(import_path)

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, RichLog
from textual.reactive import reactive
from textual.screen import Screen
from textual.containers import VerticalScroll

from shared.cli_utils import get_project_summary, get_latest_log_file

class Welcome(Static):
    """A welcome widget."""
    def on_mount(self) -> None:
        self.update("Welcome to the Agent TUI!\n\n"
                    "Press 'd' to toggle dark mode.\n"
                    "Press 'q' to quit.")

class ProjectInfo(Static):
    """A widget to display project information."""

    project_dir = reactive(Path("."))

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir

    def on_mount(self) -> None:
        """Event handler called when widget is added to the app."""
        self.update_info()
        self.set_interval(5, self.update_info)

    def update_info(self) -> None:
        """Update the project information text."""
        summary_text = get_project_summary(self.project_dir)
        self.update(summary_text)

class Dashboard(Screen):
    """The main dashboard screen for the TUI."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self._current_log_path: Path | None = None
        self._log_file_pos: int = 0

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="left-pane"):
            yield Welcome()
            yield ProjectInfo(self.project_dir, id="project-info")
        yield RichLog(id="log-viewer", wrap=True, highlight=True, max_lines=1000)
        yield Footer()

    def on_mount(self) -> None:
        """Event handler called when the screen is mounted."""
        self.query_one("#log-viewer", RichLog).write("Log viewer initialized...")
        self.set_interval(2, self.update_log_viewer)

    def update_log_viewer(self) -> None:
        """Callback to update the log viewer content."""
        log_file = get_latest_log_file()
        log_viewer = self.query_one("#log-viewer", RichLog)

        if not log_file:
            if self._current_log_path is not None:
                log_viewer.write("\nNo log file found.")
                self._current_log_path = None
                self._log_file_pos = 0
            return

        # Check if file rotated or changed
        if log_file != self._current_log_path:
            self._current_log_path = log_file
            self._log_file_pos = 0
            log_viewer.clear()
            log_viewer.write(f"Watching log: {log_file.name}")

        if log_file.exists():
            try:
                current_size = log_file.stat().st_size
                if current_size < self._log_file_pos:
                    # File was truncated or rotated
                    self._log_file_pos = 0
                    log_viewer.write("\nLog file was truncated/rotated.")

                if current_size > self._log_file_pos:
                    with open(log_file, "r", encoding="utf-8") as f:
                        f.seek(self._log_file_pos)
                        new_content = f.read()
                        self._log_file_pos = f.tell()
                        if new_content:
                            log_viewer.write(new_content)
            except Exception as e:
                log_viewer.write(f"\nError reading log file: {e}")


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
