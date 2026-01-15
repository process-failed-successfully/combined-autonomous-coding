from pathlib import Path
import_path = str(Path(__file__).parent.parent)
import sys
sys.path.append(import_path)

import asyncio
import subprocess
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, RichLog, Button
from textual.reactive import reactive
from textual.screen import Screen
from textual.containers import VerticalScroll, Horizontal

from shared.cli_utils import get_project_summary, get_latest_log_file, get_suggestions

class Welcome(Static):
    """A welcome widget."""
    def on_mount(self) -> None:
        self.update("Welcome to the Agent TUI!\n\n"
                    "Press 'd' to toggle dark mode.\n"
                    "Press 'h' for help.\n"
                    "Press 'q' to quit.")

class CommandOutput(Static):
    """A widget to display command output."""
    def on_mount(self) -> None:
        self.update("Press 't' to run tests.")

    def update_output(self, output: str) -> None:
        self.update(output)

class SuggestedActions(Static):
    """A widget to display suggested actions."""
    def on_mount(self) -> None:
        self.update_suggestions()
        self.set_interval(15, self.update_suggestions)

    def update_suggestions(self) -> None:
        project_dir = self.app.project_dir
        suggestions = get_suggestions(project_dir)
        if suggestions:
            formatted_suggestions = "\n".join([f"- {s['command']}" for s in suggestions])
            self.update(f"Suggested Actions:\n{formatted_suggestions}")
        else:
            self.update("No suggestions at the moment.")

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

    BINDINGS = [
        ("t", "run_tests", "Run tests"),
        ("l", "run_linter", "Run linter"),
        ("f", "run_formatter", "Run formatter"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main-container"):
            with VerticalScroll(id="left-pane"):
                yield Welcome()
                yield ProjectInfo(self.project_dir, id="project-info")
                yield CommandOutput(id="command-output")
                yield SuggestedActions(id="suggested-actions")
            yield RichLog(id="log-viewer", wrap=True, highlight=True)
        yield Footer()

    def on_mount(self) -> None:
        """Event handler called when the screen is mounted."""
        self.query_one("#log-viewer", RichLog).write("Log viewer initialized...")
        self.set_interval(2, self.update_log_viewer)

    async def run_command(self, command: list[str], output_widget: Static) -> None:
        output_widget.update(f"Running '{' '.join(command)}'...")
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self.project_dir
        )
        stdout, stderr = await process.communicate()
        result = stdout.decode() + stderr.decode()
        output_widget.update(result)

    async def action_run_tests(self) -> None:
        """Callback to run tests."""
        command_output_widget = self.query_one("#command-output", CommandOutput)
        await self.run_command(["./run_tests.sh"], command_output_widget)

    async def action_run_linter(self) -> None:
        """Callback to run linter."""
        # Assuming the linter command is `lint`
        # This can be adjusted to the actual command
        command_output_widget = self.query_one("#command-output", CommandOutput)
        await self.run_command(["main.py", "lint"], command_output_widget)

    async def action_run_formatter(self) -> None:
        """Callback to run formatter."""
        # Assuming the formatter command is `format`
        # This can be adjusted to the actual command
        command_output_widget = self.query_one("#command-output", CommandOutput)
        await self.run_command(["main.py", "format"], command_output_widget)

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


class HelpScreen(Screen):
    """A help screen for the TUI."""
    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("TUI Help\n\n"
                     "d: Toggle dark mode\n"
                     "h: Show this help screen\n"
                     "t: Run tests\n"
                     "l: Run linter\n"
                     "f: Run formatter\n"
                     "q: Quit\n\n"
                     "Press any key to return to the dashboard.",
                     id="help-text")
        yield Footer()

    def on_key(self) -> None:
        self.app.pop_screen()

class AgentTUI(App):
    """A Textual user interface for the autonomous coding agent."""

    CSS_PATH = "tui.css"
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("h", "show_help", "Help"),
        ("q", "quit", "Quit"),
    ]

    def action_show_help(self) -> None:
        """Show the help screen."""
        self.push_screen(HelpScreen())

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
