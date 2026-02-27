from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Input, RichLog, Label
from textual import on
from rich.text import Text
from shared.shell_lab import ShellLabManager

class ShellLabTab(Container):
    """Tab for persistent shell terminal."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = ShellLabManager(project_dir)
        self.output_buffer = ""

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Shell Lab[/bold]", classes="welcome-text")
            yield RichLog(id="shell-log", wrap=True, highlight=False, markup=False, auto_scroll=True)
            yield Input(placeholder="Type command...", id="shell-input")

    def on_mount(self) -> None:
        try:
            self.manager.start_shell(self.on_output)
            self.query_one("#shell-input").focus()

            # Send initial resize (rough estimate)
            # Textual doesn't expose terminal size easily here without more work,
            # but we can default or update on resize events later.
            self.manager.resize(24, 80)
        except RuntimeError as e:
            self.query_one("#shell-log", RichLog).write(Text(str(e), style="bold red"))
            self.query_one("#shell-input").disabled = True

    def on_unmount(self) -> None:
        self.manager.close()

    def on_output(self, data: str) -> None:
        """Callback from ShellLabManager thread."""
        # Must schedule UI update on main thread
        self.app.call_from_thread(self.write_to_log, data)

    def write_to_log(self, data: str) -> None:
        log = self.query_one("#shell-log", RichLog)

        # Handle basic ANSI stripping for now?
        # Rich Text.from_ansi handles colors well.
        text = Text.from_ansi(data)
        log.write(text)

    @on(Input.Submitted, "#shell-input")
    def on_input(self, event: Input.Submitted) -> None:
        cmd = event.value
        event.input.value = ""

        # Send to shell (append newline)
        self.manager.write(cmd + "\n")

    def on_resize(self, event) -> None:
        # Try to resize PTY if possible
        # This is tricky because Container resize isn't exactly terminal resize
        # But we can try using the log size
        try:
            log = self.query_one("#shell-log")
            width = log.size.width
            height = log.size.height
            if width and height:
                self.manager.resize(height, width)
        except Exception:
            pass
