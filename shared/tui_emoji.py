from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Label, Input, Button, DataTable
from textual.widgets import TabPane
from textual import on

from shared.emoji_lab import EmojiLabManager

class EmojiLabTab(TabPane):
    """Textual Tab for Emoji Lab functionality."""

    def __init__(self, **kwargs):
        super().__init__("Emoji Lab", id="tab-emoji", **kwargs)
        self.manager = EmojiLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Emoji Search & Discovery[/bold]", classes="welcome-text")

            with Horizontal(classes="stat-box"):
                yield Input(placeholder="Search for an emoji...", id="input-emoji-search")
                yield Button("Search", id="btn-emoji-search", variant="primary")
                yield Button("Random", id="btn-emoji-random", variant="success")
                yield Button("List All", id="btn-emoji-list", variant="default")

            yield DataTable(id="table-emoji")

    def on_mount(self):
        table = self.query_one("#table-emoji", DataTable)
        table.add_columns("Emoji", "Name", "Code")
        # Load some initial content
        self.display_results(self.manager.list_all(limit=50))

    @on(Button.Pressed, "#btn-emoji-search")
    def on_search(self):
        query = self.query_one("#input-emoji-search", Input).value
        if not query:
            return
        results = self.manager.search(query)
        self.display_results(results)

    @on(Input.Submitted, "#input-emoji-search")
    def on_search_submit(self, event: Input.Submitted):
        query = event.value
        if not query:
            return
        results = self.manager.search(query)
        self.display_results(results)

    @on(Button.Pressed, "#btn-emoji-random")
    def on_random(self):
        result = self.manager.random()
        self.display_results([result])
        self.query_one("#input-emoji-search", Input).value = ""

    @on(Button.Pressed, "#btn-emoji-list")
    def on_list(self):
        results = self.manager.list_all(limit=100)
        self.display_results(results)
        self.query_one("#input-emoji-search", Input).value = ""

    def display_results(self, results):
        table = self.query_one("#table-emoji", DataTable)
        table.clear()
        for name, char in results:
            table.add_row(char, name, f":{name}:")
