from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Input, Label, ListView, ListItem, TextArea
from textual import on

from shared.clipboard_lab import ClipboardManager

class ClipboardTab(Container):
    """Tab for managing clipboard history."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = ClipboardManager(project_dir)
        self.selected_text = None

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Clipboard Manager[/bold]", classes="welcome-text")

            # Input Area
            with Horizontal(classes="stat-box"):
                yield Input(placeholder="Enter text to copy...", id="clip-input")
                yield Button("Copy", id="btn-clip-copy", variant="primary")
                yield Button("Paste (Sync)", id="btn-clip-sync", variant="warning")

            with Horizontal():
                # History List
                with Vertical(id="clip-list-container", classes="stat-box"):
                    yield Label("[bold]History[/bold]")
                    yield ListView(id="clip-history-list")
                    yield Button("Clear History", id="btn-clip-clear", variant="error")

                # Details
                with Vertical(id="clip-details-container", classes="stat-box"):
                    yield Label("[bold]Content[/bold]")
                    yield TextArea(id="clip-content-area", read_only=True)
                    yield Button("Copy Selected to System", id="btn-clip-copy-selected", variant="success", disabled=True)

    def on_mount(self) -> None:
        self.load_history()

    def load_history(self) -> None:
        list_view = self.query_one("#clip-history-list", ListView)
        list_view.clear()

        history = self.manager.get_history()
        for item in history:
            text = item['text']
            preview = text.replace('\n', ' ')
            if len(preview) > 40:
                preview = preview[:37] + "..."

            list_item = ListItem(Label(preview))
            # Store full text in the item
            list_item.full_text = text
            list_view.append(list_item)

    @on(ListView.Selected, "#clip-history-list")
    def on_item_selected(self, event: ListView.Selected) -> None:
        if hasattr(event.item, "full_text"):
            self.selected_text = event.item.full_text
            self.query_one("#clip-content-area", TextArea).text = self.selected_text
            self.query_one("#btn-clip-copy-selected").disabled = False

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-clip-copy":
            self.copy_input()
        elif event.button.id == "btn-clip-sync":
            self.sync_clipboard()
        elif event.button.id == "btn-clip-clear":
            self.clear_history()
        elif event.button.id == "btn-clip-copy-selected":
            self.copy_selected()

    def copy_input(self) -> None:
        text = self.query_one("#clip-input", Input).value
        if not text:
            self.notify("Input empty.", severity="error")
            return

        if self.manager.copy_to_system(text):
            self.notify("Copied to clipboard.")
            self.query_one("#clip-input", Input).value = ""
            self.load_history()
        else:
            self.notify("Failed to copy.", severity="error")

    def sync_clipboard(self) -> None:
        text = self.manager.paste_from_system()
        if text:
            self.manager.add_to_history(text)
            self.load_history()
            self.notify("Synced from clipboard.")
        else:
            self.notify("Clipboard empty or inaccessible.", severity="warning")

    def clear_history(self) -> None:
        self.manager.clear_history()
        self.load_history()
        self.query_one("#clip-content-area", TextArea).text = ""
        self.query_one("#btn-clip-copy-selected").disabled = True
        self.notify("History cleared.")

    def copy_selected(self) -> None:
        if not self.selected_text:
            return

        if self.manager.copy_to_system(self.selected_text):
            self.notify("Copied selected text to system clipboard.")
            # Refresh history to move it to top
            self.load_history()
        else:
            self.notify("Failed to copy.", severity="error")
