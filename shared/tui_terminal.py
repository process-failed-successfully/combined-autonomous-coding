import asyncio
import os
from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Input, RichLog, Label
from textual.containers import Container, Vertical
from textual.binding import Binding
from rich.text import Text


class HistoryInput(Input):
    """Input widget with history navigation."""

    BINDINGS = [
        Binding("up", "history_up", "Previous Command", priority=True),
        Binding("down", "history_down", "Next Command", priority=True),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.history = []
        self.history_index = -1
        self.current_input = ""

    def action_history_up(self):
        if not self.history:
            return

        if self.history_index == -1:
            self.current_input = self.value
            self.history_index = len(self.history) - 1
        elif self.history_index > 0:
            self.history_index -= 1

        self.value = self.history[self.history_index]
        self.cursor_position = len(self.value)

    def action_history_down(self):
        if self.history_index == -1:
            return

        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.value = self.history[self.history_index]
        else:
            self.history_index = -1
            self.value = self.current_input

        self.cursor_position = len(self.value)

    def add_to_history(self, command: str):
        if command and (not self.history or self.history[-1] != command):
            self.history.append(command)
        self.history_index = -1
        self.current_input = ""


class TerminalTab(Container):
    """Tab for running shell commands."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.cwd = project_dir
        self.cmd_running = False

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(f"[bold]Terminal[/bold] (CWD: {self.cwd})", id="terminal-header", classes="welcome-text")
            yield RichLog(id="terminal-log", wrap=True, highlight=False, markup=True)
            yield HistoryInput(placeholder="Enter command...", id="terminal-input")

    def on_mount(self) -> None:
        log = self.query_one("#terminal-log", RichLog)
        log.write("Welcome to Agent Terminal.")
        log.write(f"Current directory: {self.cwd}")
        self.query_one("#terminal-input").focus()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        command = event.value.strip()
        if not command:
            return

        inp = self.query_one("#terminal-input", HistoryInput)
        inp.add_to_history(command)
        inp.value = ""

        if self.cmd_running:
            self.notify("Command already running.", severity="warning")
            return

        log = self.query_one("#terminal-log", RichLog)
        log.write(Text(f"$ {command}", style="bold green"))

        # Handle 'cd' internally
        if command.startswith("cd ") or command == "cd":
            await self.handle_cd(command)
            return

        # Handle 'clear'
        if command == "clear":
            log.clear()
            return

        # Execute command
        self.cmd_running = True
        inp.disabled = True

        try:
            await self.run_command(command)
        finally:
            self.cmd_running = False
            inp.disabled = False
            inp.focus()

    async def handle_cd(self, command: str) -> None:
        parts = command.split(maxsplit=1)
        target = parts[1] if len(parts) > 1 else "~"

        # Expand user
        target = os.path.expanduser(target)

        try:
            new_path = (self.cwd / target).resolve()
            if not new_path.exists():
                self.write_error(f"cd: {target}: No such file or directory")
            elif not new_path.is_dir():
                self.write_error(f"cd: {target}: Not a directory")
            else:
                self.cwd = new_path
                self.query_one("#terminal-header", Label).update(f"[bold]Terminal[/bold] (CWD: {self.cwd})")
        except Exception as e:
            self.write_error(f"cd: {e}")

    async def run_command(self, command: str) -> None:
        log = self.query_one("#terminal-log", RichLog)

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=self.cwd,
                env=os.environ.copy()
            )

            while True:
                if process.stdout:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    # Attempt to decode as utf-8, handle errors
                    decoded = line.decode('utf-8', errors='replace').rstrip()
                    # Use Text.from_ansi to handle colors
                    log.write(Text.from_ansi(decoded))
                else:
                    break

            await process.wait()
            if process.returncode != 0:
                log.write(Text(f"Exited with code {process.returncode}", style="bold red"))

        except Exception as e:
            self.write_error(f"Execution error: {e}")

    def write_error(self, message: str) -> None:
        log = self.query_one("#terminal-log", RichLog)
        log.write(Text(message, style="bold red"))
