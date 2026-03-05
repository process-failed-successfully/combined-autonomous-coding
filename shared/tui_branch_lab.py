from pathlib import Path

from textual.app import ComposeResult
from textual.widgets import Label, Button, DataTable, Input, Checkbox
from textual.containers import Container, Horizontal, Vertical
from textual import on

from shared.branch_lab import BranchLabManager


class BranchLabTab(Container):
    """Tab for managing Git branches."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = BranchLabManager(project_dir)
        self.branches_cache = []
        self.selected_branches = set()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Git Branch Manager[/bold]", classes="welcome-text")

            with Horizontal(classes="stat-box"):
                yield Button("Refresh", id="btn-branch-refresh", variant="primary")
                yield Button("Checkout Selected", id="btn-branch-checkout", variant="success", disabled=True)
                yield Button("Delete Selected", id="btn-branch-delete", variant="error", disabled=True)
                yield Button("Clean Merged", id="btn-branch-clean", variant="warning")
                yield Checkbox("Force Delete", id="chk-branch-force")
                yield Input(placeholder="Filter branches...", id="branch-filter")

            yield DataTable(id="branch-table")

    def on_mount(self) -> None:
        table = self.query_one("#branch-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Select", "Name", "Type", "Merged", "Date", "Author")
        self.load_branches()

    def load_branches(self) -> None:
        table = self.query_one("#branch-table", DataTable)
        table.clear()
        self.selected_branches.clear()
        self._update_buttons()

        self.branches_cache = self.manager.get_all_branches()
        self._update_table()

    def _update_table(self) -> None:
        table = self.query_one("#branch-table", DataTable)
        table.clear()

        filter_text = self.query_one("#branch-filter", Input).value.lower()

        for i, branch in enumerate(self.branches_cache):
            if filter_text and filter_text not in branch["name"].lower() and filter_text not in branch["author"].lower():
                continue

            merged_fmt = "[green]Yes[/green]" if branch["merged"] == "Yes" else "[red]No[/red]"
            selected_fmt = "[green]✓[/green]" if i in self.selected_branches else "[ ]"

            table.add_row(
                selected_fmt,
                branch["name"],
                branch["type"],
                merged_fmt,
                branch["date"],
                branch["author"],
                key=str(i)
            )

    @on(Input.Changed, "#branch-filter")
    def on_filter_changed(self) -> None:
        self._update_table()

    @on(DataTable.RowSelected, "#branch-table")
    def on_row_selected(self, event: DataTable.RowSelected) -> None:
        index = int(event.row_key.value)
        table = self.query_one("#branch-table", DataTable)
        if index in self.selected_branches:
            self.selected_branches.remove(index)
            table.update_cell(event.row_key, "Select", "[ ]")
        else:
            self.selected_branches.add(index)
            table.update_cell(event.row_key, "Select", "[green]✓[/green]")

        self._update_buttons()

    def _update_buttons(self) -> None:
        checkout_btn = self.query_one("#btn-branch-checkout", Button)
        delete_btn = self.query_one("#btn-branch-delete", Button)

        checkout_btn.disabled = len(self.selected_branches) != 1
        delete_btn.disabled = len(self.selected_branches) == 0

    @on(Button.Pressed, "#btn-branch-refresh")
    def on_refresh(self) -> None:
        self.load_branches()
        self.notify("Branches refreshed.")

    @on(Button.Pressed, "#btn-branch-checkout")
    def on_checkout(self) -> None:
        if len(self.selected_branches) != 1:
            return

        index = list(self.selected_branches)[0]
        branch_name = self.branches_cache[index]["name"]

        self.notify(f"Checking out {branch_name}...")
        success = self.manager.checkout(branch_name)
        if success:
            self.notify(f"Successfully checked out {branch_name}")
            self.load_branches()
        else:
            self.notify(f"Failed to checkout {branch_name}", severity="error")

    @on(Button.Pressed, "#btn-branch-delete")
    def on_delete_selected(self) -> None:
        if not self.selected_branches:
            return

        force = self.query_one("#chk-branch-force", Checkbox).value
        branches_to_delete = [self.branches_cache[i]["name"] for i in self.selected_branches]

        self.notify(f"Deleting {len(branches_to_delete)} branches...")

        results = self.manager.delete_branches(branches_to_delete, force=force)

        success_count = sum(1 for v in results.values() if v)
        fail_count = len(results) - success_count

        if fail_count > 0:
            self.notify(f"Deleted {success_count} branches. Failed to delete {fail_count}.", severity="warning")
        else:
            self.notify(f"Successfully deleted {success_count} branches.")

        self.load_branches()

    @on(Button.Pressed, "#btn-branch-clean")
    def on_clean_merged(self) -> None:
        force = self.query_one("#chk-branch-force", Checkbox).value
        branches_to_delete = [
            b["name"] for b in self.branches_cache
            if b["merged"] == "Yes" and b["type"] == "Local" and b["name"] not in ["main", "master"]
        ]

        if not branches_to_delete:
            self.notify("No local merged branches found to clean.")
            return

        self.notify(f"Cleaning {len(branches_to_delete)} merged branches...")

        results = self.manager.delete_branches(branches_to_delete, force=force)

        success_count = sum(1 for v in results.values() if v)
        fail_count = len(results) - success_count

        if fail_count > 0:
            self.notify(f"Cleaned {success_count} merged branches. Failed: {fail_count}.", severity="warning")
        else:
            self.notify(f"Successfully cleaned {success_count} merged branches.")

        self.load_branches()
