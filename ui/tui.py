from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Log, Button, Input
from textual.containers import Container, Vertical
from textual.worker import Worker
from textual.screen import ModalScreen
from textual.widgets import Label
from pathlib import Path
import asyncio
import sys
import argparse

sys.path.append(str(Path(__file__).parent.parent))
from shared.cli_utils import _run_summary_logic
from main import _run_clean_logic, run_agent_task, run_plan
from shared.config import Config

class RunAgentScreen(ModalScreen):
    """A modal screen for configuring and running the agent."""

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Run Agent")
            yield Input(value="gemini", id="agent_id", placeholder="Agent (e.g., gemini)")
            yield Input(id="spec_file", placeholder="Spec file (e.g., app_spec.txt)")
            yield Button("Run", variant="primary", id="run")
            yield Button("Cancel", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run":
            agent = self.query_one("#agent_id", Input).value
            spec_file = self.query_one("#spec_file", Input).value
            self.dismiss({"agent": agent, "spec_file": spec_file})
        else:
            self.dismiss(None)

class ConfirmationScreen(ModalScreen):
    """A modal screen to confirm an action."""

    def __init__(self, message: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.message = message

    def compose(self) -> ComposeResult:
        yield Container(
            Label(self.message),
            Button("Confirm", variant="primary", id="confirm"),
            Button("Cancel", id="cancel"),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "confirm")


class LogViewer(Static):
    """A widget to display and tail a log file."""

    def __init__(self, log_file: Path, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.log_file = log_file
        self.log_widget = Log()

    def compose(self) -> ComposeResult:
        yield self.log_widget

    def on_mount(self) -> None:
        self.tail_log_file()

    def tail_log_file(self) -> None:
        self.log_widget.clear()
        if self.log_file and self.log_file.exists():
            self.run_worker(self._tail_file(), exclusive=True)
        else:
            self.log_widget.write_line("No log file found to tail.")

    async def _tail_file(self) -> None:
        self.log_widget.write_line(f"--- Tailing log file: {self.log_file} ---")
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                f.seek(0, 2)
                while self.is_running:
                    line = f.readline()
                    if line:
                        self.log_widget.write_line(line.strip())
                    await asyncio.sleep(0.1)
        except Exception as e:
            self.log_widget.write_line(f"Error tailing log file: {e}")


class ProjectInfo(Static):
    """A widget to display project summary information."""
    def __init__(self, project_dir: Path, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.project_dir = project_dir

    def on_mount(self) -> None:
        self.update_summary()

    def update_summary(self) -> None:
        summary_text = _run_summary_logic(self.project_dir)
        self.update(summary_text)


class ActionButtons(Static):
    """A widget with buttons to trigger agent actions."""
    def compose(self) -> ComposeResult:
        yield Button("Run Agent", id="run_agent", variant="primary")
        yield Button("Run Plan", id="run_plan")
        yield Button("Clean Artifacts", id="clean", variant="warning")
        yield Button("Exit TUI", id="exit", variant="error")


class TuiApp(App):
    """A Textual application for the autonomous coding agent."""
    CSS_PATH = "tui.css"
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("r", "refresh_summary", "Refresh Summary"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self, project_dir: Path = Path("."), *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.project_dir = project_dir
        self.log_file = self._find_latest_log()

    def _find_latest_log(self) -> Path | None:
        repo_root = Path(__file__).parent.parent
        logs_dir = repo_root / "agents/logs"
        if not logs_dir.exists():
            return None
        log_files = list(logs_dir.glob("*.log"))
        if not log_files:
            return None
        return max(log_files, key=lambda p: p.stat().st_mtime)

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="main-container"):
            with Container(id="left-pane"):
                yield ProjectInfo(self.project_dir)
                yield ActionButtons()
            with Container(id="right-pane"):
                yield LogViewer(self.log_file)
        yield Footer()

    async def _run_agent_task(self, agent: str, spec_file: str) -> None:
        """Wrapper for run_agent_task to allow mocking."""
        config = Config(project_dir=self.project_dir, agent_type=agent)
        args = argparse.Namespace(
            project_dir=self.project_dir, agent=agent,
            spec=Path(spec_file) if spec_file else None,
            jira_ticket=None, jira_label=None, dashboard_url=None,
        )
        await run_agent_task(config, args)

    async def _run_plan(self) -> None:
        """Wrapper for run_plan to allow mocking."""
        args = argparse.Namespace(
            spec=Path("app_spec.txt") if Path("app_spec.txt").exists() else None,
            project_dir=self.project_dir, agent="gemini", model=None,
            verbose=False, profile=None,
        )
        await run_plan(args)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "exit":
            self.exit()
        elif event.button.id == "clean":
            self.confirm_and_clean()
        elif event.button.id == "run_agent":
            def on_run_agent_screen_dismiss(result: dict) -> None:
                if result:
                    self.run_worker(self.execute_run_agent(result["agent"], result["spec_file"]), exclusive=True)
            self.push_screen(RunAgentScreen(), on_run_agent_screen_dismiss)
        elif event.button.id == "run_plan":
            self.run_worker(self.execute_run_plan(), exclusive=True)

    async def execute_run_agent(self, agent: str, spec_file: str) -> None:
        log_viewer = self.query_one(LogViewer)
        log_viewer.log_widget.write_line(f"--- Starting Agent (Agent: {agent}, Spec: {spec_file}) ---")
        await self._run_agent_task(agent, spec_file)
        log_viewer.log_widget.write_line("--- Agent Finished ---")
        self.query_one(ProjectInfo).update_summary()

    async def execute_run_plan(self) -> None:
        log_viewer = self.query_one(LogViewer)
        log_viewer.log_widget.write_line("--- Starting Planner ---")
        await self._run_plan()
        log_viewer.log_widget.write_line("--- Planner Finished ---")
        self.query_one(ProjectInfo).update_summary()


    def confirm_and_clean(self) -> None:
        def check_confirmation(confirmed: bool) -> None:
            if confirmed:
                result = _run_clean_logic(self.project_dir, force=True)
                self.query_one(ProjectInfo).update_summary()
                self.query_one(LogViewer).log_widget.write_line(f"Clean result: {result}")

        self.push_screen(ConfirmationScreen("Permanently delete all agent artifacts?"), check_confirmation)

    def action_refresh_summary(self) -> None:
        self.query_one(ProjectInfo).update_summary()

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark


if __name__ == "__main__":
    app = TuiApp()
    app.run()
