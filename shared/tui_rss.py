import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import asyncio
import webbrowser

from textual.app import ComposeResult
from textual.widgets import Label, Button, ListView, ListItem, Input, RichLog, Static
from textual.containers import Container, Horizontal, Vertical
from textual import on
from rich.markup import escape

from shared.rss_lab import RssLabManager

class RssLabTab(Container):
    """Tab for RSS Feed Reader."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = RssLabManager()
        self.feeds_file = self.project_dir / ".rss_feeds.json"
        self.feeds: List[str] = []
        self.current_feed_data: Optional[Dict[str, Any]] = None
        self.selected_feed_url: Optional[str] = None
        self.current_link: Optional[str] = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: Feed List
            with Vertical(id="rss-feed-list-container", classes="stat-box"):
                yield Label("[bold]Feeds[/bold]")
                yield ListView(id="rss-feed-list")

                with Horizontal():
                    yield Input(placeholder="Add Feed URL...", id="rss-new-url")
                    yield Button("Add", id="btn-rss-add", variant="primary")

                yield Button("Remove Selected", id="btn-rss-remove", variant="error", disabled=True)
                yield Button("Refresh", id="btn-rss-refresh", variant="default", disabled=True)

            # Middle Pane: Items List
            with Vertical(id="rss-items-container", classes="stat-box"):
                yield Label("[bold]Feed Items[/bold]", id="rss-feed-title")
                yield ListView(id="rss-item-list")

            # Right Pane: Item Details
            with Vertical(id="rss-details-container"):
                yield Label("[bold]Item Details[/bold]")
                yield RichLog(id="rss-item-log", wrap=True, highlight=True, markup=True)
                yield Button("Open Link", id="btn-rss-open", variant="warning", disabled=True)

    def on_mount(self) -> None:
        self.load_feeds()
        self.populate_feed_list()

    def load_feeds(self) -> None:
        if self.feeds_file.exists():
            try:
                content = self.feeds_file.read_text(encoding="utf-8")
                self.feeds = json.loads(content)
            except Exception:
                self.feeds = []
        else:
            self.feeds = []

    def save_feeds(self) -> None:
        try:
            self.feeds_file.write_text(json.dumps(self.feeds, indent=2), encoding="utf-8")
        except Exception as e:
            self.notify(f"Error saving feeds: {e}", severity="error")

    def populate_feed_list(self) -> None:
        list_view = self.query_one("#rss-feed-list", ListView)
        list_view.clear()

        for url in self.feeds:
            list_view.append(ListItem(Label(url), name=url))

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-rss-add":
            await self.add_feed()
        elif event.button.id == "btn-rss-remove":
            self.remove_feed()
        elif event.button.id == "btn-rss-refresh":
            await self.refresh_feed()
        elif event.button.id == "btn-rss-open":
            self.open_link()

    async def add_feed(self) -> None:
        inp = self.query_one("#rss-new-url", Input)
        url = inp.value.strip()

        if not url:
            self.notify("URL required.", severity="error")
            return

        if url in self.feeds:
            self.notify("Feed already exists.", severity="warning")
            return

        self.feeds.append(url)
        self.save_feeds()
        self.populate_feed_list()
        inp.value = ""
        self.notify(f"Added feed: {url}")

    def remove_feed(self) -> None:
        if not self.selected_feed_url:
            return

        if self.selected_feed_url in self.feeds:
            self.feeds.remove(self.selected_feed_url)
            self.save_feeds()
            self.populate_feed_list()
            self.selected_feed_url = None
            self.query_one("#btn-rss-remove").disabled = True
            self.query_one("#btn-rss-refresh").disabled = True
            self.query_one("#rss-item-list", ListView).clear()
            self.query_one("#rss-item-log", RichLog).clear()
            self.notify("Feed removed.")

    @on(ListView.Selected, "#rss-feed-list")
    async def on_feed_selected(self, event: ListView.Selected) -> None:
        # Use name if available, else try to get from label
        # In populate_feed_list we set name=url.
        if event.item and hasattr(event.item, "name") and event.item.name:
            self.selected_feed_url = event.item.name
            self.query_one("#btn-rss-remove").disabled = False
            self.query_one("#btn-rss-refresh").disabled = False
            await self.refresh_feed()

    async def refresh_feed(self) -> None:
        if not self.selected_feed_url:
            return

        self.notify(f"Fetching {self.selected_feed_url}...")
        self.query_one("#rss-feed-title", Label).update(f"Loading {self.selected_feed_url}...")

        # Run in thread
        feed_data = await asyncio.to_thread(self.manager.fetch, self.selected_feed_url)

        if not feed_data:
            self.notify("Failed to fetch feed.", severity="error")
            self.query_one("#rss-feed-title", Label).update("Error loading feed.")
            return

        self.current_feed_data = feed_data
        self.populate_items()

    def populate_items(self) -> None:
        if not self.current_feed_data:
            return

        feed = self.current_feed_data.get("feed", {})
        title = feed.get("title", self.selected_feed_url)
        self.query_one("#rss-feed-title", Label).update(f"[bold]{title}[/bold]")

        items_list = self.query_one("#rss-item-list", ListView)
        items_list.clear()

        entries = self.current_feed_data.get("entries", [])
        for i, entry in enumerate(entries):
            item_title = entry.get("title", "No Title")
            # Store index as name/key
            items_list.append(ListItem(Label(item_title), name=str(i)))

    @on(ListView.Selected, "#rss-item-list")
    def on_item_selected(self, event: ListView.Selected) -> None:
        if not self.current_feed_data:
            return

        try:
            index = int(event.item.name)
            entries = self.current_feed_data.get("entries", [])
            if 0 <= index < len(entries):
                entry = entries[index]
                self.show_item_details(entry)
        except (ValueError, TypeError, IndexError, AttributeError):
            pass

    def show_item_details(self, entry: Dict[str, Any]) -> None:
        log = self.query_one("#rss-item-log", RichLog)
        log.clear()

        title = entry.get("title", "No Title")
        link = entry.get("link", "")
        date_str = entry.get("published", entry.get("updated", "N/A"))
        author = entry.get("author", "Unknown Author")
        description = entry.get("description", entry.get("summary", ""))

        log.write(f"[bold size=18]{escape(title)}[/bold size=18]")
        log.write(f"[italic]Date: {escape(date_str)} | Author: {escape(author)}[/italic]")
        log.write(f"[blue underline]{escape(link)}[/blue underline]")
        log.write("")

        # Write description (raw)
        log.write(description)

        self.query_one("#btn-rss-open").disabled = False
        self.current_link = link

    def open_link(self) -> None:
        if hasattr(self, "current_link") and self.current_link:
            try:
                webbrowser.open(self.current_link)
                self.notify(f"Opened {self.current_link}")
            except Exception as e:
                self.notify(f"Error opening link: {e}", severity="error")
