import sys
from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Label, Button, DataTable, RichLog, TextArea, TabbedContent, TabPane, Input
from textual.containers import Container, Horizontal, Vertical
from textual import on
from rich.syntax import Syntax
import asyncio
import re

from shared.git import (
    get_git_log, get_commit_details, get_git_status, stage_file, unstage_file,
    commit_changes, discard_changes, pull_changes, push_branch, get_file_diff,
    get_git_stash_list, get_stash_show, stash_push, stash_pop, stash_drop, stash_apply
)

class GitTab(Container):
    """Tab for viewing and managing Git."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.selected_file = None
        self.selected_stash = None
        self.git_status_cache = {}

    def compose(self) -> ComposeResult:
        with TabbedContent():
            with TabPane("Operations"):
                with Vertical():
                    with Horizontal(classes="git-ops-top"):
                        # Left: Status
                        with Vertical(classes="stat-box"):
                            yield Label("[bold]Changed Files[/bold]")
                            yield DataTable(id="git-status-table")
                            with Horizontal():
                                yield Button("Stage", id="btn-git-stage", variant="success")
                                yield Button("Unstage", id="btn-git-unstage", variant="warning")
                                yield Button("Discard", id="btn-git-discard", variant="error")
                            yield Button("Refresh Status", id="btn-git-refresh-status", variant="default")

                        # Right: Commit & Sync
                        with Vertical(classes="stat-box"):
                            yield Label("[bold]Commit[/bold]")
                            yield TextArea(id="git-commit-msg")
                            yield Button("Commit", id="btn-git-commit", variant="primary")

                            yield Label("[bold]Sync[/bold]")
                            with Horizontal():
                                yield Button("Pull", id="btn-git-pull", variant="default")
                                yield Button("Push", id="btn-git-push", variant="warning")
                            yield Label("", id="git-sync-status")

                    # Bottom: Diff
                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Diff[/bold]")
                        yield RichLog(id="git-ops-diff-view", wrap=True, highlight=True, markup=False)

            with TabPane("Stash"):
                with Horizontal():
                    # Left: Stash List & Actions
                    with Vertical(id="git-stash-list-container", classes="stat-box"):
                        yield Label("[bold]Stashes[/bold]")
                        yield DataTable(id="git-stash-table")

                        yield Label("New Stash:")
                        with Horizontal():
                            yield Input(placeholder="Message...", id="git-stash-msg")
                            yield Button("Push", id="btn-stash-push", variant="primary")

                        yield Label("Actions on Selected:")
                        with Horizontal():
                            yield Button("Pop", id="btn-stash-pop", variant="warning", disabled=True)
                            yield Button("Apply", id="btn-stash-apply", variant="success", disabled=True)
                            yield Button("Drop", id="btn-stash-drop", variant="error", disabled=True)

                        yield Button("Refresh", id="btn-stash-refresh", variant="default")

                    # Right: Stash Diff
                    with Vertical(id="git-stash-diff-container", classes="stat-box"):
                        yield Label("[bold]Stash Diff[/bold]")
                        yield RichLog(id="git-stash-diff-view", wrap=True, highlight=True, markup=False)

            with TabPane("History"):
                with Horizontal():
                    with Vertical(id="git-list-container", classes="stat-box"):
                        yield Label("[bold]Git History[/bold]")
                        yield DataTable(id="git-log-table")
                        yield Button("Refresh", id="btn-refresh-git", variant="default")

                    with Vertical(id="git-details-container"):
                        yield Label("[bold]Commit Details[/bold]")
                        yield RichLog(id="git-details-view", wrap=True, highlight=True, markup=False)

    def on_mount(self) -> None:
        # History Table
        history_table = self.query_one("#git-log-table", DataTable)
        history_table.cursor_type = "row"
        history_table.add_columns("Hash", "Date", "Author", "Message")
        self.load_history()

        # Status Table
        status_table = self.query_one("#git-status-table", DataTable)
        status_table.cursor_type = "row"
        status_table.add_columns("S", "Status", "Path")
        self.load_status()

        # Stash Table
        stash_table = self.query_one("#git-stash-table", DataTable)
        stash_table.cursor_type = "row"
        stash_table.add_columns("Index", "Message")
        self.load_stashes()

    def load_history(self) -> None:
        table = self.query_one("#git-log-table", DataTable)
        table.clear()

        logs = get_git_log(self.project_dir)
        for log in logs:
            table.add_row(
                log["hash"],
                log["date"],
                log["author"],
                log["message"]
            )

    def load_status(self) -> None:
        table = self.query_one("#git-status-table", DataTable)
        table.clear()
        self.git_status_cache = {}

        try:
            files = get_git_status(self.project_dir)
            for f in files:
                staged_marker = "[green]✓[/green]" if f["staged"] else "[red] [/red]"
                status_code = f["status_code"]
                path = f["path"]
                self.git_status_cache[path] = f
                # Store full path in key
                table.add_row(staged_marker, status_code, path, key=path)
        except Exception as e:
            self.notify(f"Error loading status: {e}", severity="error")

    def load_stashes(self) -> None:
        table = self.query_one("#git-stash-table", DataTable)
        table.clear()

        # Disable buttons
        self.query_one("#btn-stash-pop").disabled = True
        self.query_one("#btn-stash-apply").disabled = True
        self.query_one("#btn-stash-drop").disabled = True
        self.selected_stash = None
        self.query_one("#git-stash-diff-view", RichLog).clear()

        try:
            stashes = get_git_stash_list(self.project_dir)
            for s in stashes:
                table.add_row(s["name"], s["message"], key=s["name"])
        except Exception as e:
            self.notify(f"Error loading stashes: {e}", severity="error")

    @on(Button.Pressed, "#btn-refresh-git")
    def on_refresh_history(self) -> None:
        self.load_history()
        self.notify("Git history refreshed.")

    @on(Button.Pressed, "#btn-git-refresh-status")
    def on_refresh_status(self) -> None:
        self.load_status()
        self.notify("Git status refreshed.")

    @on(Button.Pressed, "#btn-stash-refresh")
    def on_refresh_stashes(self) -> None:
        self.load_stashes()
        self.notify("Stashes refreshed.")

    @on(DataTable.RowSelected, "#git-log-table")
    def on_history_selected(self, event: DataTable.RowSelected) -> None:
        table = self.query_one("#git-log-table", DataTable)
        row_values = table.get_row(event.row_key)
        commit_hash = row_values[0]

        details = get_commit_details(self.project_dir, commit_hash)
        viewer = self.query_one("#git-details-view", RichLog)
        viewer.clear()
        viewer.write(details)

    @on(DataTable.RowSelected, "#git-status-table")
    def on_status_selected(self, event: DataTable.RowSelected) -> None:
        self.selected_file = event.row_key.value

        # Show diff
        diff_view = self.query_one("#git-ops-diff-view", RichLog)
        diff_view.clear()

        if not self.selected_file:
            return

        file_info = self.git_status_cache.get(self.selected_file)
        if not file_info:
            return

        is_staged = file_info.get("staged", False)

        asyncio.create_task(self._load_diff(self.selected_file, is_staged))

    @on(DataTable.RowSelected, "#git-stash-table")
    def on_stash_selected(self, event: DataTable.RowSelected) -> None:
        self.selected_stash = event.row_key.value # stash@{n}

        # Enable buttons
        self.query_one("#btn-stash-pop").disabled = False
        self.query_one("#btn-stash-apply").disabled = False
        self.query_one("#btn-stash-drop").disabled = False

        # Load diff
        diff = get_stash_show(self.project_dir, self.selected_stash)
        view = self.query_one("#git-stash-diff-view", RichLog)
        view.clear()
        if diff.strip():
            view.write(Syntax(diff, "diff", theme="monokai"))
        else:
            view.write("No content.")

    async def _load_diff(self, file_path: str, staged: bool) -> None:
        diff_view = self.query_one("#git-ops-diff-view", RichLog)
        diff_view.clear()
        diff_view.write("Loading diff...")

        diff = await asyncio.to_thread(get_file_diff, self.project_dir, file_path, staged)

        diff_view.clear()
        if diff.strip():
            diff_view.write(Syntax(diff, "diff", theme="monokai"))
        else:
            diff_view.write("No diff available (possibly binary or empty).")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-git-stage":
            self.stage_selected()
        elif event.button.id == "btn-git-unstage":
            self.unstage_selected()
        elif event.button.id == "btn-git-discard":
            self.discard_selected()
        elif event.button.id == "btn-git-commit":
            self.commit()
        elif event.button.id == "btn-git-pull":
            await self.pull()
        elif event.button.id == "btn-git-push":
            await self.push()
        elif event.button.id == "btn-stash-push":
            self.push_stash()
        elif event.button.id == "btn-stash-pop":
            self.pop_stash()
        elif event.button.id == "btn-stash-apply":
            self.apply_stash()
        elif event.button.id == "btn-stash-drop":
            self.drop_stash()

    def stage_selected(self) -> None:
        if not self.selected_file:
            self.notify("No file selected.", severity="warning")
            return
        if stage_file(self.project_dir, self.selected_file):
            self.notify(f"Staged {self.selected_file}")
            self.load_status()
        else:
            self.notify("Stage failed.", severity="error")

    def unstage_selected(self) -> None:
        if not self.selected_file:
            self.notify("No file selected.", severity="warning")
            return
        if unstage_file(self.project_dir, self.selected_file):
            self.notify(f"Unstaged {self.selected_file}")
            self.load_status()
        else:
            self.notify("Unstage failed.", severity="error")

    def discard_selected(self) -> None:
        if not self.selected_file:
            self.notify("No file selected.", severity="warning")
            return
        # TODO: Confirmation dialog? Textual has ModalScreen.
        # For now, just do it with notification.
        if discard_changes(self.project_dir, self.selected_file):
            self.notify(f"Discarded changes in {self.selected_file}")
            self.load_status()
        else:
            self.notify("Discard failed.", severity="error")

    def commit(self) -> None:
        msg_area = self.query_one("#git-commit-msg", TextArea)
        msg = msg_area.text
        if not msg:
            self.notify("Commit message required.", severity="error")
            return

        if commit_changes(self.project_dir, msg):
            self.notify("Committed.")
            msg_area.text = "" # Clear
            self.load_status()
            self.load_history()
        else:
            self.notify("Commit failed.", severity="error")

    async def pull(self) -> None:
        lbl = self.query_one("#git-sync-status", Label)
        lbl.update("Pulling...")

        success = await asyncio.to_thread(pull_changes, self.project_dir)

        if success:
            lbl.update("[green]Pull Successful[/green]")
            self.notify("Pull successful.")
            self.load_history()
            self.load_status()
        else:
            lbl.update("[red]Pull Failed[/red]")
            self.notify("Pull failed.", severity="error")

    async def push(self) -> None:
        lbl = self.query_one("#git-sync-status", Label)
        lbl.update("Pushing...")

        success = await asyncio.to_thread(push_branch, self.project_dir)

        if success:
            lbl.update("[green]Push Successful[/green]")
            self.notify("Push successful.")
        else:
            lbl.update("[red]Push Failed[/red]")
            self.notify("Push failed.", severity="error")

    def push_stash(self) -> None:
        msg_inp = self.query_one("#git-stash-msg", Input)
        msg = msg_inp.value
        if not msg:
            msg = "WIP"

        if stash_push(self.project_dir, msg):
            self.notify("Stashed changes.")
            msg_inp.value = ""
            self.load_stashes()
            self.load_status() # Stashing cleans status
        else:
            self.notify("Stash failed.", severity="error")

    def pop_stash(self) -> None:
        if not self.selected_stash: return
        if stash_pop(self.project_dir, self.selected_stash):
            self.notify(f"Popped {self.selected_stash}")
            self.load_stashes()
            self.load_status()
        else:
            self.notify("Pop failed.", severity="error")

    def apply_stash(self) -> None:
        if not self.selected_stash: return
        if stash_apply(self.project_dir, self.selected_stash):
            self.notify(f"Applied {self.selected_stash}")
            self.load_status()
        else:
            self.notify("Apply failed.", severity="error")

    def drop_stash(self) -> None:
        if not self.selected_stash: return
        if stash_drop(self.project_dir, self.selected_stash):
            self.notify(f"Dropped {self.selected_stash}")
            self.load_stashes()
        else:
            self.notify("Drop failed.", severity="error")
