"""
Emoji Lab
=========

Utilities for searching, listing, and discovering emojis.
"""

import sys
import random
from typing import List, Tuple, Dict, Optional
from rich.console import Console
from rich.table import Table
try:
    from rich.emoji import EMOJI
except ImportError:
    from rich._emoji_codes import EMOJI

console = Console()

class EmojiLabManager:
    """Manages Emoji Lab operations."""

    def __init__(self):
        self.emojis = EMOJI

    def search(self, query: str) -> List[Tuple[str, str]]:
        """Search emojis by name (case-insensitive substring)."""
        query = query.lower()
        results = []
        for name, char in self.emojis.items():
            if query in name.lower():
                results.append((name, char))
        return sorted(results)

    def list_all(self, limit: int = 50) -> List[Tuple[str, str]]:
        """List all emojis, limited by count."""
        return list(self.emojis.items())[:limit]

    def random(self) -> Tuple[str, str]:
        """Return a random emoji."""
        name = random.choice(list(self.emojis.keys()))
        return (name, self.emojis[name])

def run_emoji_lab_logic(args):
    """CLI handler for Emoji Lab."""
    manager = EmojiLabManager()

    if args.action == "search":
        if not args.query:
            console.print("[red]Error: Query required for search.[/red]")
            return

        results = manager.search(args.query)
        if not results:
            console.print(f"[yellow]No emojis found matching '{args.query}'.[/yellow]")
            return

        table = Table(title=f"Search Results: '{args.query}'")
        table.add_column("Emoji", justify="center", style="bold")
        table.add_column("Name", style="cyan")
        table.add_column("Code", style="dim")

        for name, char in results:
            table.add_row(char, name, f":{name}:")

        console.print(table)

    elif args.action == "list":
        limit = int(args.limit) if args.limit else 50
        results = manager.list_all(limit)

        table = Table(title=f"Emoji List (First {limit})")
        table.add_column("Emoji", justify="center", style="bold")
        table.add_column("Name", style="cyan")
        table.add_column("Code", style="dim")

        for name, char in results:
            table.add_row(char, name, f":{name}:")

        console.print(table)
        if len(manager.emojis) > limit:
            console.print(f"[dim]... and {len(manager.emojis) - limit} more.[/dim]")

    elif args.action == "random":
        name, char = manager.random()
        console.print(f"[bold]{char}[/bold]  [cyan]:{name}:[/cyan]")

    else:
        console.print("[red]Unknown action.[/red]")
