import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, ListView, ListItem, Label, Static
from textual.containers import Container, Vertical
from textual.binding import Binding
from textual import on

@dataclass
class RebaseEntry:
    action: str
    commit_hash: str
    message: str
    original_line: str

    def to_line(self) -> str:
        return f"{self.action} {self.commit_hash} {self.message}"

class RebaseItem(ListItem):
    """A list item representing a rebase entry."""

    def __init__(self, entry: RebaseEntry) -> None:
        super().__init__()
        self.entry = entry
        self.update_label()

    def update_label(self) -> None:
        action_color = "white"
        if self.entry.action == "pick" or self.entry.action == "p":
            action_color = "green"
        elif self.entry.action == "reword" or self.entry.action == "r":
            action_color = "blue"
        elif self.entry.action == "edit" or self.entry.action == "e":
            action_color = "yellow"
        elif self.entry.action == "squash" or self.entry.action == "s":
            action_color = "magenta"
        elif self.entry.action == "fixup" or self.entry.action == "f":
            action_color = "cyan"
        elif self.entry.action == "drop" or self.entry.action == "d":
            action_color = "red"

        self.query(Label).remove()
        self.mount(Label(f"[{action_color}]{self.entry.action:<6}[/] [dim]{self.entry.commit_hash}[/] {self.entry.message}"))

class RebaseTUI(App):
    """Interactive Git Rebase TUI."""

    CSS = """
    RebaseItem {
        padding: 1;
        background: $surface;
    }
    RebaseItem:hover {
        background: $surface-lighten-1;
    }
    RebaseItem.-highlight {
        background: $accent;
    }
    """

    BINDINGS = [
        Binding("q,escape", "quit_app", "Abort"),
        Binding("ctrl+s", "save_and_exit", "Save & Rebase"),
        Binding("up", "move_cursor_up", "Up"),
        Binding("down", "move_cursor_down", "Down"),
        Binding("shift+up", "move_line_up", "Move Up"),
        Binding("shift+down", "move_line_down", "Move Down"),
        Binding("enter", "cycle_action", "Cycle Action"),
        Binding("p", "set_pick", "Pick"),
        Binding("r", "set_reword", "Reword"),
        Binding("e", "set_edit", "Edit"),
        Binding("s", "set_squash", "Squash"),
        Binding("f", "set_fixup", "Fixup"),
        Binding("d", "set_drop", "Drop"),
    ]

    def __init__(self, file_path: Path):
        super().__init__()
        self.file_path = file_path
        self.entries: List[RebaseEntry] = []
        self.comments: List[str] = [] # Preserve comments

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Label("[bold]Interactive Rebase[/bold] - Reorder (Shift+Up/Down) or Change Action (Enter)", classes="welcome-text")
        yield ListView(id="rebase-list")
        yield Footer()

    def on_mount(self) -> None:
        self.load_file()

    def load_file(self) -> None:
        if not self.file_path.exists():
            self.notify("File not found!", severity="error")
            return

        content = self.file_path.read_text(encoding="utf-8")
        lines = content.splitlines()

        list_view = self.query_one("#rebase-list", ListView)

        valid_actions = ["pick", "p", "reword", "r", "edit", "e", "squash", "s", "fixup", "f", "exec", "x", "break", "b", "drop", "d", "label", "l", "reset", "t", "merge", "m"]

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                self.comments.append(line)
                continue

            parts = line.split(" ", 2)
            if len(parts) >= 2 and parts[0] in valid_actions:
                action = parts[0]
                commit_hash = parts[1]
                message = parts[2] if len(parts) > 2 else ""
                entry = RebaseEntry(action, commit_hash, message, line)
                self.entries.append(entry)
                list_view.append(RebaseItem(entry))
            else:
                # Unknown line, preserve as comment? Or maybe exec?
                self.comments.append(line)

    def action_quit_app(self) -> None:
        # Abort rebase by clearing the file (git treats empty file as abort if checking content,
        # but usually it expects exit code 0 to proceed.
        # If we exit with non-zero, git aborts.
        self.exit(result=1)

    def action_save_and_exit(self) -> None:
        self.save_file()
        self.exit(result=0)

    def save_file(self) -> None:
        list_view = self.query_one("#rebase-list", ListView)
        lines = []

        # Reconstruct from ListView order
        for item in list_view.children:
            if isinstance(item, RebaseItem):
                lines.append(item.entry.to_line())

        # Append preserved comments (optional, but good for context if rebase fails)
        # Git usually ignores comments in todo list anyway
        # lines.extend(self.comments)

        content = "\n".join(lines) + "\n"
        self.file_path.write_text(content, encoding="utf-8")

    def action_move_line_up(self) -> None:
        list_view = self.query_one("#rebase-list", ListView)
        idx = list_view.index
        if idx is not None and idx > 0:
            # Move item in list view (remove and insert)
            # Textual's ListView doesn't have a simple 'move' method,
            # so we might need to rely on python list manipulation and re-rendering
            # OR messing with children directly.
            # Messing with children directly is risky.
            # Best approach: swap children

            # Swap in UI
            item = list_view.children[idx]
            list_view.remove_children([item])
            list_view.mount(item, before=list_view.children[idx-1])

            # Update selection
            list_view.index = idx - 1

    def action_move_line_down(self) -> None:
        list_view = self.query_one("#rebase-list", ListView)
        idx = list_view.index
        if idx is not None and idx < len(list_view.children) - 1:
            item = list_view.children[idx]
            list_view.remove_children([item])
            # mount after the next item
            # list_view.mount(item, after=list_view.children[idx]) # index is now old_idx (because one removed)
            # wait, if I removed at i, the one at i+1 becomes i.
            # so I want to insert at i+1.
            list_view.mount(item, at=idx+1)

            list_view.index = idx + 1

    def _set_action(self, action: str) -> None:
        list_view = self.query_one("#rebase-list", ListView)
        if list_view.index is not None:
            item = list_view.children[list_view.index]
            if isinstance(item, RebaseItem):
                item.entry.action = action
                item.update_label()

    def action_set_pick(self) -> None: self._set_action("pick")
    def action_set_reword(self) -> None: self._set_action("reword")
    def action_set_edit(self) -> None: self._set_action("edit")
    def action_set_squash(self) -> None: self._set_action("squash")
    def action_set_fixup(self) -> None: self._set_action("fixup")
    def action_set_drop(self) -> None: self._set_action("drop")

    def action_cycle_action(self) -> None:
        list_view = self.query_one("#rebase-list", ListView)
        if list_view.index is not None:
            item = list_view.children[list_view.index]
            if isinstance(item, RebaseItem):
                actions = ["pick", "reword", "edit", "squash", "fixup", "drop"]
                current = item.entry.action
                # Normalize short codes
                map_short = {"p": "pick", "r": "reword", "e": "edit", "s": "squash", "f": "fixup", "d": "drop"}
                if current in map_short: current = map_short[current]

                try:
                    idx = actions.index(current)
                    next_action = actions[(idx + 1) % len(actions)]
                except ValueError:
                    next_action = "pick"

                item.entry.action = next_action
                item.update_label()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        app = RebaseTUI(Path(sys.argv[1]))
        app.run()
    else:
        print("Error: No file provided.")
