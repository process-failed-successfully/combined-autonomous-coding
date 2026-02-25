from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, Button, Input, TextArea, ListView, ListItem
from textual import on
from shared.clipboard_lab import ClipboardManager
import json
import base64

class HistoryListItem(ListItem):
    """ListItem that holds a history index."""
    def __init__(self, *args, history_index: int = -1, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.history_index = history_index

class ClipboardTab(Container):
    """Tab for Clipboard Manager."""

    def __init__(self, project_dir=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = ClipboardManager(project_dir)
        self.selected_index = -1

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: History List
            with Vertical(id="clip-list-container", classes="stat-box"):
                yield Label("[bold]Clipboard History[/bold]")
                yield ListView(id="clip-list")
                with Horizontal():
                    yield Button("Add Manual", id="btn-clip-add", variant="primary")
                    yield Input(placeholder="Content...", id="input-clip-add")
                yield Button("Refresh", id="btn-clip-refresh", variant="default")
                yield Button("Clear All", id="btn-clip-clear", variant="error")

            # Right Pane: Preview & Actions
            with Vertical(id="clip-preview-container"):
                yield Label("[bold]Content Preview[/bold]")
                yield TextArea(id="clip-preview", language="markdown")

                with Horizontal(classes="stat-box"):
                    yield Button("Update Entry", id="btn-clip-update", variant="primary", disabled=True)
                    yield Button("Delete Selected", id="btn-clip-delete", variant="error", disabled=True)
                    yield Button("Copy to System", id="btn-clip-copy", variant="success", disabled=True)

                yield Label("[bold]Transformations[/bold]")
                with Horizontal(classes="stat-box"):
                    yield Button("UPPER", id="btn-trans-upper")
                    yield Button("lower", id="btn-trans-lower")
                    yield Button("JSON Format", id="btn-trans-json")
                    yield Button("Base64 Enc", id="btn-trans-b64e")
                    yield Button("Base64 Dec", id="btn-trans-b64d")

    def on_mount(self) -> None:
        self.load_history()

    def load_history(self) -> None:
        list_view = self.query_one("#clip-list", ListView)
        list_view.clear()

        # Sync from system first
        if self.manager.sync_system():
            self.notify("Synced from system clipboard.")

        history = self.manager.list_history()
        if not history:
            list_view.append(ListItem(Label("[dim]History is empty[/dim]")))
            return

        for i, item in enumerate(history):
            content = item["content"]
            # Truncate for list view
            preview = content.replace('\n', ' ')
            if len(preview) > 40:
                preview = preview[:37] + "..."

            label = f"[{i}] {preview}"
            list_item = HistoryListItem(Label(label), history_index=i)
            list_view.append(list_item)

    @on(ListView.Selected, "#clip-list")
    def on_item_selected(self, event: ListView.Selected) -> None:
        if not isinstance(event.item, HistoryListItem):
            return

        index = event.item.history_index
        self.selected_index = index
        content = self.manager.get(index)

        if content is not None:
            self.query_one("#clip-preview", TextArea).text = content
            self.enable_buttons()

    def enable_buttons(self) -> None:
        self.query_one("#btn-clip-update").disabled = False
        self.query_one("#btn-clip-delete").disabled = False
        self.query_one("#btn-clip-copy").disabled = False

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id

        if btn_id == "btn-clip-refresh":
            self.load_history()
            self.notify("Refreshed.")
        elif btn_id == "btn-clip-clear":
            self.manager.clear()
            self.load_history()
            self.query_one("#clip-preview", TextArea).text = ""
            self.notify("History cleared.")
        elif btn_id == "btn-clip-add":
            val = self.query_one("#input-clip-add", Input).value
            if val:
                self.manager.add(val)
                self.query_one("#input-clip-add", Input).value = ""
                self.load_history()
        elif btn_id == "btn-clip-delete":
            self.delete_selected()
        elif btn_id == "btn-clip-update":
            self.update_selected()
        elif btn_id == "btn-clip-copy":
            self.copy_to_system()

        # Transformations
        elif btn_id == "btn-trans-upper":
            self.transform_text(lambda s: s.upper())
        elif btn_id == "btn-trans-lower":
            self.transform_text(lambda s: s.lower())
        elif btn_id == "btn-trans-json":
            self.format_json()
        elif btn_id == "btn-trans-b64e":
            self.transform_text(lambda s: base64.b64encode(s.encode()).decode())
        elif btn_id == "btn-trans-b64d":
            self.transform_text(self.safe_b64_decode)

    def delete_selected(self) -> None:
        if self.selected_index < 0:
            return

        if self.manager.delete(self.selected_index):
            self.load_history()
            self.query_one("#clip-preview", TextArea).text = ""
            self.selected_index = -1
            self.notify("Item deleted.")
        else:
            self.notify("Failed to delete item.", severity="error")

    def update_selected(self) -> None:
        if self.selected_index < 0:
            return

        text = self.query_one("#clip-preview", TextArea).text
        if self.manager.update(self.selected_index, text):
            self.load_history()
            self.notify("Entry updated.")
        else:
            self.notify("Failed to update item.", severity="error")

    def copy_to_system(self) -> None:
        text = self.query_one("#clip-preview", TextArea).text
        try:
            import pyperclip
            pyperclip.copy(text)
            self.notify("Copied to system clipboard.")
        except ImportError:
            self.notify("pyperclip not installed.", severity="error")
        except Exception as e:
            self.notify(f"Error copying: {e}", severity="error")

    def transform_text(self, func) -> None:
        editor = self.query_one("#clip-preview", TextArea)
        text = editor.text
        if not text:
            return
        try:
            new_text = func(text)
            editor.text = new_text
        except Exception as e:
            self.notify(f"Transformation error: {e}", severity="error")

    def format_json(self) -> None:
        editor = self.query_one("#clip-preview", TextArea)
        text = editor.text
        try:
            obj = json.loads(text)
            new_text = json.dumps(obj, indent=2)
            editor.text = new_text
        except Exception as e:
            self.notify(f"JSON Error: {e}", severity="error")

    def safe_b64_decode(self, s: str) -> str:
        try:
            return base64.b64decode(s).decode()
        except Exception:
            return "Error: Invalid Base64"
