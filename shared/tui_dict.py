import sys
from typing import Any
from pathlib import Path
from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Label, Button, Input, RichLog
from textual.binding import Binding
from textual import work
from textual import on
from textual.message import Message
from shared.dict_lab import DictLabManager

class DictLabTab(Vertical):
    """Tab for Dictionary operations."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.manager = DictLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Dictionary Lab[/bold]", classes="welcome-text")
            yield Label("Lookup words, definitions, synonyms, and antonyms.", classes="welcome-text")

            with Horizontal(classes="stat-box"):
                yield Label("Word:", classes="label")
                yield Input(placeholder="Enter a word...", id="dict-input")
                yield Button("Define", id="btn-define", variant="primary")
                yield Button("Synonyms", id="btn-synonyms")
                yield Button("Antonyms", id="btn-antonyms")

            yield RichLog(id="dict-log", highlight=True, markup=True, wrap=True)

    @on(Button.Pressed)
    def handle_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        word = self.query_one("#dict-input", Input).value.strip()
        log = self.query_one("#dict-log", RichLog)

        if not word:
            log.write("[red]Please enter a word to lookup.[/red]")
            return

        if button_id == "btn-define":
            self.lookup_word(word, action="define")
        elif button_id == "btn-synonyms":
            self.lookup_word(word, action="synonym")
        elif button_id == "btn-antonyms":
            self.lookup_word(word, action="antonym")

    @work(thread=True)
    def lookup_word(self, word: str, action: str) -> None:
        """Runs the lookup asynchronously to not block the UI."""

        self.app.call_from_thread(self._write_to_log, f"[dim]Looking up '{word}'...[/dim]")

        # We need to run the synchronous request in a thread pool to avoid blocking
        # But we will use the existing self.manager which uses requests (blocking)
        # However @work in textual will run this in a worker thread automatically!
        result = self.manager.lookup(word)

        self.app.call_from_thread(self._handle_lookup_result, word, action, result)

    def _write_to_log(self, text: str) -> None:
        log = self.query_one("#dict-log", RichLog)
        log.write(text)

    def _handle_lookup_result(self, word: str, action: str, result: dict) -> None:
        log = self.query_one("#dict-log", RichLog)

        if not result["success"]:
            log.write(f"[bold red]Error:[/bold red] {result.get('error', 'Unknown error')}")
            return

        data = result["data"]

        if action == "define":
            definitions = self.manager.get_definitions(data)
            if not definitions:
                log.write(f"[yellow]No definitions found for '{word}'.[/yellow]")
                return

            log.write(f"\n[bold cyan]--- Definitions for: {word} ---[/bold cyan]")
            for i, d in enumerate(definitions):
                phonetic = f" ({d['phonetic']})" if d['phonetic'] else ""
                log.write(f"[magenta][{d['part_of_speech']}][/magenta]{phonetic} {d['definition']}")
                if d['example']:
                    log.write(f"  [italic]Example: \"{d['example']}\"[/italic]")

        elif action == "synonym":
            synonyms = self.manager.get_synonyms(data)
            if synonyms:
                log.write(f"\n[bold green]--- Synonyms for: {word} ---[/bold green]")
                log.write(", ".join(synonyms))
            else:
                log.write(f"[yellow]No synonyms found for '{word}'.[/yellow]")

        elif action == "antonym":
            antonyms = self.manager.get_antonyms(data)
            if antonyms:
                log.write(f"\n[bold red]--- Antonyms for: {word} ---[/bold red]")
                log.write(", ".join(antonyms))
            else:
                log.write(f"[yellow]No antonyms found for '{word}'.[/yellow]")
