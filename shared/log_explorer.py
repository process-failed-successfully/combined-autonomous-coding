import io
import contextlib
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, RichLog, ListView, ListItem, Label, Input, Button, Markdown
from textual.containers import Container, Horizontal, Vertical
from textual.binding import Binding
from textual import on
from shared.cli_utils import get_all_log_files
from shared.ask import run_ask_logic

class LogExplorerApp(App):
    """Standalone Interactive Log Explorer TUI."""

    CSS = """
    Screen {
        layout: vertical;
    }

    #sidebar {
        width: 30;
        dock: left;
        height: 100%;
        border-right: solid green;
    }

    #main-content {
        height: 100%;
        margin-left: 1;
    }

    #log-viewer {
        height: 1fr;
        border: solid blue;
    }

    #analysis-panel {
        height: 15;
        border-top: solid yellow;
        dock: bottom;
        display: none;
    }

    .stat-box {
        height: auto;
        padding: 1;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "toggle_dark", "Toggle Dark Mode"),
        ("a", "analyze_log", "Analyze with AI"),
        ("f", "focus_filter", "Filter Logs"),
    ]

    def __init__(self, project_dir: Path, agent_type: str = "gemini", **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.agent_type = agent_type
        self.current_log_path = None

    def compose(self) -> ComposeResult:
        yield Header()

        with Container():
            # Sidebar
            with Vertical(id="sidebar"):
                yield Label("[bold]Log Files[/bold]")
                yield ListView(id="log-list")
                yield Button("Refresh", id="btn-refresh", variant="default")

            # Main Content
            with Vertical(id="main-content"):
                with Horizontal(classes="stat-box"):
                    yield Label("Filter:", classes="label")
                    yield Input(placeholder="Type to filter log lines...", id="log-filter")
                    yield Button("Analyze (AI)", id="btn-analyze", variant="warning")

                yield RichLog(id="log-viewer", wrap=True, highlight=True, markup=True)

                # Analysis Panel (Bottom)
                with Vertical(id="analysis-panel"):
                    yield Label("[bold]AI Analysis[/bold]")
                    yield Markdown(id="analysis-output")

        yield Footer()

    def on_mount(self) -> None:
        self.load_logs()

    def load_logs(self) -> None:
        log_list = self.query_one("#log-list", ListView)
        log_list.clear()

        # We rely on cli_utils to find logs relative to repo root or project dir
        # But get_all_log_files uses __file__ relative path which might be tricky if shared/ is symlinked or something.
        # Let's trust it works as in tui.py
        logs = get_all_log_files()

        if not logs:
            log_list.append(ListItem(Label("No logs found")))
            return

        for log_file in logs:
            try:
                size = log_file.stat().st_size
                size_str = f"{size / 1024:.1f} KB"
                label = f"{log_file.name} ({size_str})"
            except OSError:
                label = log_file.name

            item = ListItem(Label(label))
            item.log_path = log_file
            log_list.append(item)

        # Select first
        if logs:
            log_list.index = 0
            self.load_log_content(logs[0])

    @on(ListView.Selected, "#log-list")
    def on_log_selected(self, event: ListView.Selected) -> None:
        if hasattr(event.item, "log_path"):
            self.load_log_content(event.item.log_path)

    @on(Button.Pressed, "#btn-refresh")
    def on_refresh(self) -> None:
        self.load_logs()
        self.notify("Logs refreshed.")

    @on(Input.Changed, "#log-filter")
    def on_filter_changed(self, event: Input.Changed) -> None:
        if self.current_log_path:
            self.load_log_content(self.current_log_path, filter_text=event.value)

    def load_log_content(self, file_path: Path, filter_text: str = "") -> None:
        self.current_log_path = file_path
        viewer = self.query_one("#log-viewer", RichLog)
        viewer.clear()

        self.title = f"Log Explorer - {file_path.name}"

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            if filter_text:
                lines = [l for l in lines if filter_text.lower() in l.lower()]

            # Performance optimization: truncate if too huge for TUI
            if len(lines) > 5000:
                viewer.write(f"[bold yellow]Displaying last 5000 lines of {len(lines)}...[/bold yellow]")
                lines = lines[-5000:]

            viewer.write("".join(lines))

        except Exception as e:
            viewer.write(f"[red]Error reading file: {e}[/red]")

    def action_focus_filter(self) -> None:
        self.query_one("#log-filter", Input).focus()

    async def action_analyze_log(self) -> None:
        await self.run_analysis()

    @on(Button.Pressed, "#btn-analyze")
    async def on_analyze_click(self) -> None:
        await self.run_analysis()

    async def run_analysis(self) -> None:
        if not self.current_log_path:
            self.notify("No log selected.", severity="warning")
            return

        panel = self.query_one("#analysis-panel")
        panel.styles.display = "block"

        output = self.query_one("#analysis-output", Markdown)
        output.update("Thinking... Analyzing log content for errors and summary...")
        self.notify("Asking AI to analyze log...", severity="information")

        # Read last N lines for context (don't send 10MB log)
        try:
            with open(self.current_log_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
                # Take last 300 lines or so
                context = "".join(lines[-300:])
        except Exception as e:
            output.update(f"Error reading log: {e}")
            return

        prompt = f"""
Analyze the following agent log (last 300 lines).
Identify any errors, warnings, or significant actions.
Provide a concise summary of what happened and why it might have failed (if it did).
If it succeeded, summarize the outcome.

### LOG CONTENT
{context}
"""

        # Use run_ask_logic but capture output is tricky because it prints to stdout usually.
        # But run_ask_logic actually returns the response string if we use the right pattern?
        # Wait, run_ask_logic returns (success: bool). It prints to stdout.
        # So we must capture stdout.

        capture = io.StringIO()
        success = False
        with contextlib.redirect_stdout(capture):
            try:
                success = await run_ask_logic(
                    query=prompt,
                    project_dir=self.project_dir,
                    agent_type=self.agent_type,
                    verbose=False
                )
            except Exception as e:
                print(f"Error: {e}")

        result_text = capture.getvalue()

        if success:
            output.update(result_text)
        else:
            output.update(f"**Analysis Failed**\n\n{result_text}")

if __name__ == "__main__":
    import sys
    app = LogExplorerApp(Path("."))
    app.run()
