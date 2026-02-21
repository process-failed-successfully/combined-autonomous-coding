from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, ListView, ListItem, Input, Markdown
from textual import on
from shared.cheatsheet_lab import CheatsheetManager

class CheatsheetTab(Container):
    """Tab for viewing Cheat Sheets."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = CheatsheetManager(project_dir)
        self.current_topic = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: List and Search
            with Vertical(id="cheat-list-container", classes="stat-box"):
                yield Label("[bold]Topics[/bold]")
                yield Input(placeholder="Search...", id="cheat-search")
                yield ListView(id="cheat-topic-list")

            # Right Pane: Content
            with Vertical(id="cheat-content-container"):
                yield Label("[bold]Cheatsheet[/bold]", id="cheat-header")
                yield Markdown(id="cheat-markdown")

    def on_mount(self) -> None:
        self.load_topics()

    def load_topics(self, filter_text: str = "") -> None:
        list_view = self.query_one("#cheat-topic-list", ListView)
        list_view.clear()

        topics = self.manager.list_topics()

        for topic in topics:
            if filter_text and filter_text.lower() not in topic.lower():
                continue

            # Capitalize first letter for display
            display = topic.capitalize()
            # Store topic key in the item
            item = ListItem(Label(display))
            item.topic_key = topic
            list_view.append(item)

    @on(Input.Changed, "#cheat-search")
    def on_search_changed(self, event: Input.Changed) -> None:
        self.load_topics(event.value)

    @on(ListView.Selected, "#cheat-topic-list")
    def on_topic_selected(self, event: ListView.Selected) -> None:
        if not hasattr(event.item, "topic_key"):
            return

        topic = event.item.topic_key
        self.current_topic = topic
        self.load_content(topic)

    def load_content(self, topic: str) -> None:
        content = self.manager.get_content(topic)
        if content:
            self.query_one("#cheat-markdown", Markdown).update(content)
            self.query_one("#cheat-header", Label).update(f"[bold]{topic.capitalize()} Cheatsheet[/bold]")
        else:
            self.query_one("#cheat-markdown", Markdown).update("Content not found.")
