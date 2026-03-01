from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Input, DataTable, Static, Label
from textual.widget import Widget

from shared.http_status_lab import HttpStatusLabManager

class HttpStatusLabTab(Widget):
    """A tab for searching and viewing HTTP status codes."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.manager = HttpStatusLabManager()

    def compose(self) -> ComposeResult:
        with Vertical(classes="p-4"):
            yield Label("HTTP Status Codes", classes="text-xl text-bold mb-4")

            with Horizontal(classes="h-auto mb-4"):
                yield Input(placeholder="Search by code (e.g. 404) or description (e.g. teapot)...", id="http-status-search", classes="w-full")

            yield DataTable(id="http-status-table", cursor_type="row")

            with Vertical(id="http-status-details", classes="mt-4 p-4 border border-primary hidden"):
                yield Label("", id="detail-code-message", classes="text-lg text-bold text-secondary mb-2")
                yield Label("", id="detail-category", classes="text-md mb-2")
                yield Static("", id="detail-description")

    def on_mount(self) -> None:
        table = self.query_one("#http-status-table", DataTable)
        table.add_columns("Code", "Message", "Category")
        self._populate_table()

    def _populate_table(self, query: str = "") -> None:
        table = self.query_one("#http-status-table", DataTable)
        table.clear()

        if query:
            results = self.manager.search_status(query)
        else:
            # If no query, show all
            results = [{"code": code, **details} for code, details in self.manager.STATUS_CODES.items()]

        # Sort results by code
        results.sort(key=lambda x: x["code"])

        for res in results:
            table.add_row(str(res["code"]), res["message"], res["category"], key=str(res["code"]))

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "http-status-search":
            self._populate_table(event.value)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        table = self.query_one("#http-status-table", DataTable)
        row_key = event.row_key.value
        if not row_key:
            return

        code = int(row_key)
        status_info = self.manager.get_status(code)

        if status_info:
            details_container = self.query_one("#http-status-details", Vertical)
            details_container.remove_class("hidden")

            self.query_one("#detail-code-message", Label).update(f"{code} - {status_info['message']}")
            self.query_one("#detail-category", Label).update(f"Category: {status_info['category']}")
            self.query_one("#detail-description", Static).update(status_info['description'])
