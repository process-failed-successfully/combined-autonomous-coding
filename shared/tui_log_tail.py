from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Label, Button, Input, RichLog, DirectoryTree, Checkbox
from textual.containers import Container, Horizontal, Vertical
from textual.timer import Timer
from textual import on
import os

class LogTailTab(Container):
    """Tab for real-time log tailing."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.current_file: Path | None = None
        self.file_pos = 0
        self.tail_timer: Timer | None = None
        self.is_tailing = False

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: File Selector
            with Vertical(id="log-tail-sidebar", classes="stat-box"):
                yield Label("[bold]Select Log File[/bold]")
                yield DirectoryTree(str(self.project_dir), id="log-tail-tree")

            # Right Pane: Log View
            with Vertical(id="log-tail-main"):
                with Horizontal(classes="stat-box"):
                    yield Label("File: None", id="lbl-tail-file")
                    yield Button("Start Tailing", id="btn-tail-start", variant="primary", disabled=True)
                    yield Button("Stop", id="btn-tail-stop", variant="error", disabled=True)
                    yield Button("Clear", id="btn-tail-clear", variant="default")
                    yield Checkbox("Auto-scroll", id="chk-tail-scroll", value=True)

                with Horizontal(classes="stat-box"):
                    yield Label("Highlight:")
                    yield Input(placeholder="Text to highlight...", id="input-tail-highlight")

                yield RichLog(id="log-tail-view", wrap=True, highlight=True, markup=True)

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        path = event.path
        if path.is_file():
            self.current_file = path
            self.query_one("#lbl-tail-file", Label).update(f"File: {path.name}")
            self.query_one("#btn-tail-start").disabled = False
            self.stop_tailing() # Stop previous if any
        else:
            self.current_file = None
            self.query_one("#lbl-tail-file", Label).update("File: None")
            self.query_one("#btn-tail-start").disabled = True

    @on(Button.Pressed, "#btn-tail-start")
    def on_start(self) -> None:
        self.start_tailing()

    @on(Button.Pressed, "#btn-tail-stop")
    def on_stop(self) -> None:
        self.stop_tailing()

    @on(Button.Pressed, "#btn-tail-clear")
    def on_clear(self) -> None:
        self.query_one("#log-tail-view", RichLog).clear()

    def start_tailing(self) -> None:
        if not self.current_file:
            return

        self.is_tailing = True
        self.query_one("#btn-tail-start").disabled = True
        self.query_one("#btn-tail-stop").disabled = False
        self.notify(f"Tailing {self.current_file.name}...")

        # Read entire file first (like 'cat' then 'tail -f')
        self.file_pos = 0
        self.read_new_lines()

        # Poll every 1s
        self.tail_timer = self.set_interval(1.0, self.read_new_lines)

    def stop_tailing(self) -> None:
        self.is_tailing = False
        if self.tail_timer:
            self.tail_timer.stop()
            self.tail_timer = None

        try:
            self.query_one("#btn-tail-start").disabled = False
            self.query_one("#btn-tail-stop").disabled = True
        except Exception:
            # Widget might be unmounting
            pass

    def read_new_lines(self) -> None:
        if not self.current_file or not self.current_file.exists():
            return

        try:
            current_size = self.current_file.stat().st_size
            if current_size < self.file_pos:
                # File truncated
                self.file_pos = 0
                self.query_one("#log-tail-view", RichLog).write("[bold yellow]File truncated.[/bold yellow]")

            if current_size > self.file_pos:
                with open(self.current_file, "r", encoding="utf-8", errors="replace") as f:
                    f.seek(self.file_pos)
                    lines = f.readlines()
                    self.file_pos = f.tell()

                log_view = self.query_one("#log-tail-view", RichLog)
                highlight = self.query_one("#input-tail-highlight", Input).value
                auto_scroll = self.query_one("#chk-tail-scroll", Checkbox).value

                for line in lines:
                    line = line.rstrip()
                    if highlight and highlight in line:
                        # Simple highlight
                        line = line.replace(highlight, f"[bold reverse yellow]{highlight}[/bold reverse yellow]")

                    log_view.write(line, scroll_end=auto_scroll)

        except Exception as e:
            self.stop_tailing()
            self.notify(f"Error reading file: {e}", severity="error")

    def on_unmount(self) -> None:
        self.stop_tailing()
