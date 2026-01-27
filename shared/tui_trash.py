from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, Button, DataTable, RichLog
from textual import on
from shared.trash import TrashManager

class TrashTab(Container):
    """Tab for managing trashed files."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = TrashManager(project_dir)
        self.selected_trash_id = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: List
            with Vertical(id="trash-list-container", classes="stat-box"):
                yield Label("[bold]Trash Bin[/bold]")
                yield DataTable(id="trash-table")
                yield Button("Refresh", id="btn-trash-refresh", variant="default")

            # Right Pane: Details & Actions
            with Vertical(id="trash-details-container"):
                yield Label("[bold]Details[/bold]")
                yield RichLog(id="trash-log", wrap=True, highlight=True, markup=True)

                with Horizontal(id="trash-actions", classes="stat-box"):
                    yield Button("Restore", id="btn-trash-restore", variant="success", disabled=True)
                    yield Button("Delete Permanently", id="btn-trash-delete", variant="error", disabled=True)
                    yield Button("Empty Trash", id="btn-trash-empty", variant="error")

    def on_mount(self) -> None:
        table = self.query_one("#trash-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Time", "Original Path", "Name")
        self.load_trash()

    def load_trash(self) -> None:
        table = self.query_one("#trash-table", DataTable)
        table.clear()

        items = self.manager.list_trash()
        for item in items:
            # item has id, original_path, filename, time
            table.add_row(
                item["time"],
                item["original_path"],
                item["filename"],
                key=item["id"]
            )

        self.selected_trash_id = None
        self._update_buttons()
        self.query_one("#trash-log", RichLog).clear()

    def _update_buttons(self) -> None:
        has_sel = self.selected_trash_id is not None
        self.query_one("#btn-trash-restore").disabled = not has_sel
        self.query_one("#btn-trash-delete").disabled = not has_sel

    @on(DataTable.RowSelected, "#trash-table")
    def on_trash_selected(self, event: DataTable.RowSelected) -> None:
        self.selected_trash_id = event.row_key.value
        self._update_buttons()

        log = self.query_one("#trash-log", RichLog)
        log.clear()

        # Find item details
        items = self.manager.list_trash()
        item = next((i for i in items if i["id"] == self.selected_trash_id), None)

        if item:
            log.write(f"[bold]ID:[/bold] {item['id']}")
            log.write(f"[bold]Original Path:[/bold] {item['original_path']}")
            log.write(f"[bold]Time:[/bold] {item['time']}")
            log.write(f"[bold]Type:[/bold] {'Directory' if item['is_dir'] else 'File'}")

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id

        if btn_id == "btn-trash-refresh":
            self.load_trash()
            self.notify("Trash refreshed.")

        elif btn_id == "btn-trash-restore":
            self.restore_selected()

        elif btn_id == "btn-trash-delete":
            self.delete_selected()

        elif btn_id == "btn-trash-empty":
            self.empty_trash()

    def restore_selected(self) -> None:
        if not self.selected_trash_id:
            return

        try:
            if self.manager.restore(self.selected_trash_id):
                self.notify("Restored successfully.")
                self.load_trash()
            else:
                self.notify("Restore failed.", severity="error")
        except FileExistsError:
            self.notify("Target path already exists. Delete it first.", severity="error")
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    def delete_selected(self) -> None:
        if not self.selected_trash_id:
            return

        try:
            if self.manager.delete_trash_item(self.selected_trash_id):
                self.notify("Deleted permanently.")
                self.load_trash()
            else:
                self.notify("Deletion failed.", severity="error")
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    def empty_trash(self) -> None:
        try:
            self.manager.empty_trash()
            self.notify("Trash emptied.")
            self.load_trash()
        except Exception as e:
            self.notify(f"Error emptying trash: {e}", severity="error")
