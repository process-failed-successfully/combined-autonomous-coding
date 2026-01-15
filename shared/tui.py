from pathlib import Path
import_path = str(Path(__file__).parent.parent)
import sys
import io
import contextlib
import threading
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, RichLog, Input
from textual.reactive import reactive
from textual.screen import Screen
from textual.containers import Vertical, Horizontal

# Make sure the main module can be imported
if import_path not in sys.path:
    sys.path.append(import_path)

# Import CLI utility functions and the main parser
from shared.cli_utils import get_project_summary, get_latest_log_file
import main as cli_main


class Welcome(Static):
    """A welcome widget with instructions."""
    def on_mount(self) -> None:
        self.update("Welcome to the Agent TUI!\n\n"
                    "Type commands in the box below and press Enter.\n"
                    "Supported: status, test, lint, format, list-agents\n\n"
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

class CommandRunner(Static):
    """A widget for running CLI commands."""
    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        yield RichLog(id="command-output", wrap=True, highlight=True)
        yield Input(placeholder="Enter command...")

    def on_mount(self) -> None:
        self.query_one("#command-output", RichLog).write("Command output initialized...")

    def _run_command_in_thread(self, command: str):
        """Runs the command in a background thread and updates the UI."""
        output_log = self.query_one("#command-output", RichLog)

        SUPPORTED_COMMANDS = {
            "status": cli_main.run_status,
            "test": cli_main.run_test,
            "lint": cli_main.run_lint,
            "format": cli_main.run_format,
            "list-agents": cli_main.run_list_agents,
        }

        def target():
            output_capture = io.StringIO()
            try:
                with contextlib.redirect_stdout(output_capture), contextlib.redirect_stderr(output_capture):
                    parts = command.split()
                    command_name = parts[0]

                    # This will raise SystemExit on unknown commands, which is caught below
                    args = cli_main.parse_args([command_name, "--project-dir", str(self.project_dir)])

                    if command_name in SUPPORTED_COMMANDS:
                        SUPPORTED_COMMANDS[command_name](args)
                    else:
                        # This should not be reachable if parse_args is working correctly
                        output_capture.write(f"Error: Command '{command_name}' is not supported by the TUI runner.")

            except SystemExit as e:
                # Argparse will write its error message to stderr (which we've redirected)
                # and then call sys.exit(). We just catch the exit here.
                # We can add the exit code for clarity if it's not 0.
                if e.code != 0 and str(e.code) not in output_capture.getvalue():
                     output_capture.write(f"\nCommand exited with code: {e.code}")
            except Exception as e:
                output_capture.write(f"\nAn unexpected TUI error occurred: {e}")
            finally:
                result = output_capture.getvalue()
                self.app.call_from_thread(output_log.write, result)

        # Clear the log for the new command's output
        output_log.clear()
        output_log.write(f"$ {command}")

        # Start the thread
        thread = threading.Thread(target=target)
        thread.start()

    async def on_input_submitted(self, message: Input.Submitted) -> None:
        """Handle the user submitting a command."""
        command = message.value
        if command:
            self._run_command_in_thread(command)
            message.input.clear()


class Dashboard(Screen):
    """The main dashboard screen for the TUI."""
    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main-container"):
            with Vertical(id="left-pane"):
                yield Welcome(id="welcome")
                yield ProjectInfo(self.project_dir, id="project-info")
                yield CommandRunner(self.project_dir, id="command-runner")
            yield RichLog(id="log-viewer", wrap=True, highlight=True)
        yield Footer()

    def on_mount(self) -> None:
        """Event handler called when the screen is mounted."""
        self.query_one("#log-viewer", RichLog).write("Log viewer initialized...")
        self.set_interval(2, self.update_log_viewer)

    def update_log_viewer(self) -> None:
        """Callback to update the agent log viewer content."""
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
            log_viewer.write("No agent log file found.")


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
