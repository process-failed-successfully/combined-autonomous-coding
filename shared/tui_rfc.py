from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, Input, Button, DataTable, RichLog
from textual import on
from shared.rfc_lab import RFCLabManager
from pathlib import Path
import asyncio

class RFCLabTab(Container):
    """Tab for searching and reading IETF RFCs."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = RFCLabManager(project_dir)

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: Search
            with Vertical(id="rfc-search-container", classes="stat-box"):
                yield Label("[bold]RFC Search[/bold]")
                with Horizontal():
                    yield Input(placeholder="Search keywords...", id="rfc-search-input")
                    yield Button("Search", id="btn-rfc-search", variant="primary")

                yield DataTable(id="rfc-results-table")
                yield Button("Update Index", id="btn-rfc-update", variant="warning")

            # Right Pane: Content
            with Vertical(id="rfc-content-container"):
                yield Label("[bold]RFC Content[/bold]")
                yield RichLog(id="rfc-content-log", wrap=True, highlight=True, markup=False)

    def on_mount(self) -> None:
        table = self.query_one("#rfc-results-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Number", "Title")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-rfc-search":
            await self.perform_search()
        elif event.button.id == "btn-rfc-update":
            await self.update_index()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "rfc-search-input":
            await self.perform_search()

    async def perform_search(self) -> None:
        query = self.query_one("#rfc-search-input", Input).value
        if not query:
            self.notify("Search query required.", severity="error")
            return

        self.notify("Searching RFCs...")
        table = self.query_one("#rfc-results-table", DataTable)
        table.clear()

        # Run in thread
        results = await asyncio.to_thread(self.manager.search, query)

        if not results:
            self.notify("No results found.")
            return

        for r in results:
            table.add_row(r["number"], r["title"], key=r["number"])

        self.notify(f"Found {len(results)} RFCs.")

    async def update_index(self) -> None:
        self.notify("Updating RFC Index... (this may take a while)", severity="information")
        success = await asyncio.to_thread(self.manager.update_index, True)
        if success:
            self.notify("Index updated.")
        else:
            self.notify("Failed to update index.", severity="error")

    @on(DataTable.RowSelected, "#rfc-results-table")
    async def on_rfc_selected(self, event: DataTable.RowSelected) -> None:
        number = event.row_key.value
        await self.load_rfc(number)

    async def load_rfc(self, number: str) -> None:
        self.notify(f"Loading RFC {number}...")
        log = self.query_one("#rfc-content-log", RichLog)
        log.clear()
        log.write(f"Loading RFC {number}...")

        content = await asyncio.to_thread(self.manager.get_rfc, number)

        log.clear()
        if content:
            log.write(content)
        else:
            log.write(f"Failed to load RFC {number}.")
            self.notify("Failed to load RFC.", severity="error")
