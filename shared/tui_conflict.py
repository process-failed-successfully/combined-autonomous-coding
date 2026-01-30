from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Label, Button, ListView, ListItem, RichLog
from textual.containers import Container, Horizontal, Vertical
from textual import on
from rich.syntax import Syntax
import asyncio

from shared.conflict_resolver import ConflictResolver, Conflict

class ConflictTab(Container):
    """Tab for Interactive Conflict Resolution."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.resolver = ConflictResolver(project_dir)
        self.conflicted_files = []
        self.selected_file = None
        self.current_conflicts = []
        self.current_conflict_index = 0

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: File List
            with Vertical(id="conflict-list-container", classes="stat-box"):
                yield Label("[bold]Conflicted Files[/bold]")
                yield ListView(id="conflict-file-list")
                yield Button("Refresh", id="btn-conflict-refresh", variant="default")

            # Right Pane: Resolution Interface
            with Vertical(id="conflict-details-container"):
                yield Label("[bold]Conflict Resolution[/bold]")

                # Navigation & Actions
                with Horizontal(classes="stat-box"):
                    yield Button("Prev", id="btn-conflict-prev")
                    yield Label("0/0", id="lbl-conflict-counter")
                    yield Button("Next", id="btn-conflict-next")

                    yield Button("Accept Current", id="btn-resolve-ours", variant="success")
                    yield Button("Accept Incoming", id="btn-resolve-theirs", variant="primary")
                    yield Button("AI Resolve (File)", id="btn-resolve-ai", variant="warning")

                # Content View
                yield RichLog(id="conflict-view", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        self.refresh_list()

    def refresh_list(self) -> None:
        self.conflicted_files = self.resolver.find_conflicted_files()
        list_view = self.query_one("#conflict-file-list", ListView)
        list_view.clear()

        for f in self.conflicted_files:
            rel_path = f.relative_to(self.project_dir)
            list_view.append(ListItem(Label(str(rel_path))))

        if not self.conflicted_files:
            self.query_one("#conflict-view", RichLog).clear()
            self.query_one("#conflict-view", RichLog).write("No conflicted files found.")
            self.query_one("#lbl-conflict-counter", Label).update("0/0")
            self.selected_file = None
            self.current_conflicts = []

    @on(ListView.Selected, "#conflict-file-list")
    def on_file_selected(self, event: ListView.Selected) -> None:
        index = self.query_one("#conflict-file-list", ListView).index
        if index is not None and index < len(self.conflicted_files):
            self.selected_file = self.conflicted_files[index]
            self.load_file_conflicts()

    def load_file_conflicts(self) -> None:
        if not self.selected_file or not self.selected_file.exists():
            return

        content = self.selected_file.read_text(encoding="utf-8", errors="replace")
        self.current_conflicts = self.resolver.parse_conflicts(content)
        self.current_conflict_index = 0

        self.update_view()

    def update_view(self) -> None:
        log = self.query_one("#conflict-view", RichLog)
        log.clear()

        counter = self.query_one("#lbl-conflict-counter", Label)
        if not self.current_conflicts:
            counter.update("0/0")
            if self.selected_file:
                content = self.selected_file.read_text(encoding="utf-8", errors="replace")
                log.write("File is clean (no conflict markers found).")
                log.write(Syntax(content, "python", theme="monokai"))
            return

        # Ensure index is valid
        if self.current_conflict_index >= len(self.current_conflicts):
            self.current_conflict_index = 0

        counter.update(f"{self.current_conflict_index + 1}/{len(self.current_conflicts)}")

        content = self.selected_file.read_text(encoding="utf-8", errors="replace")
        lines = content.splitlines()

        target_conflict = self.current_conflicts[self.current_conflict_index]

        log.write(f"[bold]Conflict {self.current_conflict_index + 1} of {len(self.current_conflicts)}[/bold]\n")

        # Show context (5 lines before and after)
        start = max(0, target_conflict.start_line - 5)
        end = min(len(lines), target_conflict.end_line + 6)

        for i in range(start, end):
            line = lines[i]
            style = ""

            # Determine styling based on conflict regions
            if target_conflict.start_line <= i <= target_conflict.end_line:
                if line.startswith("<<<<<<<"):
                    style = "[bold red]"
                elif line.startswith("======="):
                    style = "[bold red]"
                elif line.startswith(">>>>>>>"):
                    style = "[bold red]"
                elif line.startswith("|||||||"):
                    style = "[bold red]"

                # Correct Logic for Diff3 (Base) and Standard
                sep_line = target_conflict.sep_line
                base_line = target_conflict.base_line

                ours_end = base_line if base_line is not None else sep_line

                if target_conflict.start_line < i < ours_end:
                    # Ours (Current)
                    style = "[green]"
                elif base_line is not None and base_line < i < sep_line:
                    # Base (Diff3)
                    style = "[dim]"
                elif sep_line < i < target_conflict.end_line:
                    # Theirs (Incoming)
                    style = "[blue]"

            # Escape brackets in content to avoid markup errors
            safe_line = line.replace("[", "\\[")

            log.write(f"{i+1:4} | {style}{safe_line}[/]")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id

        if btn_id == "btn-conflict-refresh":
            self.refresh_list()
        elif btn_id == "btn-conflict-prev":
            if self.current_conflicts:
                self.current_conflict_index = max(0, self.current_conflict_index - 1)
                self.update_view()
        elif btn_id == "btn-conflict-next":
            if self.current_conflicts:
                self.current_conflict_index = min(len(self.current_conflicts) - 1, self.current_conflict_index + 1)
                self.update_view()
        elif btn_id == "btn-resolve-ours":
            self.resolve_current("ours")
        elif btn_id == "btn-resolve-theirs":
            self.resolve_current("theirs")
        elif btn_id == "btn-resolve-ai":
            await self.resolve_ai()

    def resolve_current(self, strategy: str) -> None:
        if not self.selected_file or not self.current_conflicts:
            self.notify("No conflict selected.", severity="warning")
            return

        success = self.resolver.resolve_manual(self.selected_file, self.current_conflict_index, strategy)
        if success:
            self.notify(f"Resolved using {strategy}")
            self.load_file_conflicts() # Reload to reflect changes and new indices
        else:
            self.notify("Resolution failed", severity="error")

    async def resolve_ai(self) -> None:
        if not self.selected_file:
            self.notify("No file selected.", severity="warning")
            return

        self.notify("AI is resolving...", severity="information")

        try:
            result = await self.resolver.resolve_file(self.selected_file, agent_type="gemini")

            if result["resolved"]:
                self.resolver.apply_resolution(self.selected_file, result["resolved_content"])
                self.notify("AI Resolution Applied")
                self.load_file_conflicts()
            else:
                self.notify(f"AI Resolution Failed: {result.get('message')}", severity="error")
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")
