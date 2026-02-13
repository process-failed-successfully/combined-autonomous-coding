import sys
from typing import Dict, Any, Optional
import json

try:
    import feedparser
except ImportError:
    feedparser = None

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich import box
    from rich.syntax import Syntax
except ImportError:
    Console = None
    Table = None
    Panel = None
    Text = None
    box = None
    Syntax = None


class RssLabManager:
    """
    Manages RSS/Atom feed operations.
    """
    def __init__(self):
        if not feedparser:
            print("Error: 'feedparser' library not found. Please install it with 'pip install feedparser'.", file=sys.stderr)
            sys.exit(1)
        self.console = Console() if Console else None

    def fetch(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Fetches and parses a feed from a URL.
        """
        try:
            feed = feedparser.parse(url)
            # feedparser always returns a dict, even on error it might contain 'bozo_exception'
            if feed.bozo:
                # We can warn but still try to use what we parsed
                if self.console:
                    self.console.print(f"[yellow]Warning: Feed parsing had issues: {feed.bozo_exception}[/yellow]")
                else:
                    print(f"Warning: Feed parsing had issues: {feed.bozo_exception}", file=sys.stderr)

            return feed
        except Exception as e:
            if self.console:
                self.console.print(f"[red]Error fetching feed: {e}[/red]")
            else:
                print(f"Error fetching feed: {e}", file=sys.stderr)
            return None

    def display_feed(self, feed_data: Dict[str, Any], limit: int = 10):
        """
        Displays the feed entries in a nice table.
        """
        if not feed_data:
            return

        feed = feed_data.get("feed", {})
        entries = feed_data.get("entries", [])

        title = feed.get("title", "Unknown Feed")
        description = feed.get("description", "No description")
        link = feed.get("link", "")

        if self.console:
            # Header
            self.console.print(Panel(
                Text(description, style="italic"),
                title=f"[bold cyan]{title}[/bold cyan] ({link})",
                border_style="blue"
            ))

            # Entries Table
            table = Table(box=box.SIMPLE, show_header=True, header_style="bold magenta")
            table.add_column("Date", style="green", width=20)
            table.add_column("Title", style="bold white")
            table.add_column("Link", style="blue")

            for entry in entries[:limit]:
                # Try to find a date
                date_str = entry.get("published", entry.get("updated", "N/A"))

                # Truncate title if too long
                entry_title = entry.get("title", "No Title")

                entry_link = entry.get("link", "")

                table.add_row(date_str, entry_title, entry_link)

            self.console.print(table)
            self.console.print(f"\n[dim]Showing {min(len(entries), limit)} of {len(entries)} entries.[/dim]")

        else:
            # Fallback for no rich
            print(f"--- {title} ---")
            print(f"Link: {link}")
            print(f"Description: {description}\n")
            print(f"Entries (Limit: {limit}):")
            for entry in entries[:limit]:
                date_str = entry.get("published", entry.get("updated", "N/A"))
                print(f"[{date_str}] {entry.get('title')} - {entry.get('link')}")

    def inspect_feed(self, feed_data: Dict[str, Any]):
        """
        Displays raw feed structure.
        """
        if not feed_data:
            return

        # We assume rich is available if we passed init, but double check
        if self.console:
            entries = feed_data.get("entries", [])
            first_entry = entries[0] if entries else None

            # Create a simplified dictionary for display to avoid circular refs or huge output
            debug_view = {
                "feed": feed_data.get("feed"),
                "headers": feed_data.get("headers"),
                "status": feed_data.get("status"),
                "version": feed_data.get("version"),
                "encoding": feed_data.get("encoding"),
                "entries_count": len(entries),
                "first_entry": first_entry
            }

            formatted_json = json.dumps(debug_view, indent=2, default=str)
            syntax = Syntax(formatted_json, "json", theme="monokai", line_numbers=True)
            self.console.print(syntax)
        else:
            print(feed_data)


def run_rss_lab_logic(args):
    """
    CLI Entry point for RSS Lab.
    """
    manager = RssLabManager()

    if args.action == "read":
        if not args.url:
            print("Error: URL required.", file=sys.stderr)
            sys.exit(1)

        feed = manager.fetch(args.url)
        if feed:
            manager.display_feed(feed, limit=args.limit)

    elif args.action == "inspect":
        if not args.url:
            print("Error: URL required.", file=sys.stderr)
            sys.exit(1)

        feed = manager.fetch(args.url)
        if feed:
            manager.inspect_feed(feed)

    sys.exit(0)
