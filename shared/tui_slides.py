from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Markdown, ProgressBar, Label
from textual.containers import Container, Vertical
from textual.binding import Binding
from textual.reactive import reactive
import sys

from shared.slides_lab import SlideDeck

class SlidesApp(App):
    """
    A TUI for presenting Markdown slides.
    """
    CSS = """
    SlideView {
        height: 1fr;
        padding: 2;
        content-align: center middle;
    }

    Markdown {
        height: 100%;
        margin: 2 4;
    }

    ProgressBar {
        dock: bottom;
        width: 100%;
        height: 1;
        margin-bottom: 1;
    }

    #slide-counter {
        dock: bottom;
        width: 100%;
        text-align: right;
        padding-right: 2;
        color: $text-muted;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("right", "next_slide", "Next"),
        ("space", "next_slide", "Next"),
        ("left", "prev_slide", "Previous"),
        ("backspace", "prev_slide", "Previous"),
        ("d", "toggle_dark", "Toggle Dark Mode"),
        ("home", "first_slide", "First"),
        ("end", "last_slide", "Last"),
    ]

    current_slide_index = reactive(0)

    def __init__(self, filepath: Path, theme: str = "default"):
        super().__init__()
        self.deck = SlideDeck(filepath)
        try:
            self.deck.load()
        except FileNotFoundError:
            print(f"Error: File '{filepath}' not found.")
            sys.exit(1)
        self.theme_name = theme

    def compose(self) -> ComposeResult:
        yield Header()
        with Container():
            yield Markdown("", id="slide-content")
        yield Label("", id="slide-counter")
        yield ProgressBar(total=len(self.deck), show_eta=False, show_percentage=False)
        yield Footer()

    def on_mount(self) -> None:
        self.update_slide()
        # Set theme if applicable (not fully implemented in deck parsing yet, but placeholder)
        self.title = f"Slides: {self.deck.filepath.name}"

    def update_slide(self) -> None:
        content = self.deck.get_slide(self.current_slide_index)
        self.query_one("#slide-content", Markdown).update(content)

        # Update Progress
        progress = self.query_one(ProgressBar)
        progress.progress = self.current_slide_index + 1

        # Update Counter
        counter = self.query_one("#slide-counter", Label)
        counter.update(f"{self.current_slide_index + 1} / {len(self.deck)}")

    def action_next_slide(self) -> None:
        if self.current_slide_index < len(self.deck) - 1:
            self.current_slide_index += 1
            self.update_slide()
        else:
            self.notify("End of presentation.")

    def action_prev_slide(self) -> None:
        if self.current_slide_index > 0:
            self.current_slide_index -= 1
            self.update_slide()

    def action_first_slide(self) -> None:
        self.current_slide_index = 0
        self.update_slide()

    def action_last_slide(self) -> None:
        self.current_slide_index = len(self.deck) - 1
        self.update_slide()

def run_slides_lab_logic(args):
    """
    CLI entry point for Slides Lab.
    """
    path = Path(args.file).resolve()
    app = SlidesApp(path, theme=args.theme)
    app.run()
