from pathlib import Path
import asyncio
from typing import Optional
from textual.app import ComposeResult
from textual.widgets import Label, Input, Button, ListView, ListItem, TextArea, RichLog
from textual.containers import Container, Horizontal, Vertical
from textual import on
from shared.redis_lab import RedisLabManager
import json


class RedisLabTab(Container):
    """
    Redis Management Tab.
    Supports key browsing, value inspection/editing, and basic management.
    """

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        # Default manager, URL will be set on connect
        self.manager = RedisLabManager()
        self.current_key: Optional[str] = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: Connection & Keys
            with Vertical(id="redis-sidebar", classes="stat-box"):
                yield Label("[bold]Redis[/bold]")

                # Connection
                yield Label("URL:")
                yield Input(value="redis://localhost:6379/0", id="redis-url-input")
                yield Button("Connect", id="btn-redis-connect", variant="primary")
                yield Label("Not Connected", id="lbl-redis-status", classes="status-text")

                # Keys
                yield Label("[bold]Keys[/bold]")
                with Horizontal():
                    yield Input(placeholder="Pattern (*)", value="*", id="redis-pattern-input")
                    yield Button("Go", id="btn-redis-scan", variant="default")

                yield ListView(id="redis-key-list")

            # Right Pane: Inspector & Editor
            with Vertical(id="redis-main"):
                # Header Info
                with Horizontal(classes="stat-box"):
                    with Vertical():
                        yield Label("Key:", classes="label")
                        yield Label("None", id="lbl-redis-key", classes="value")
                    with Vertical():
                        yield Label("Type:", classes="label")
                        yield Label("-", id="lbl-redis-type", classes="value")
                    with Vertical():
                        yield Label("TTL:", classes="label")
                        yield Label("-", id="lbl-redis-ttl", classes="value")

                # Value Editor
                yield Label("[bold]Value[/bold]")
                yield TextArea(id="redis-value-editor", language="json")

                # Actions
                with Horizontal(classes="stat-box"):
                    yield Button("Save Value", id="btn-redis-save", variant="success", disabled=True)
                    yield Button("Delete Key", id="btn-redis-delete", variant="error", disabled=True)
                    yield Button("Refresh Key", id="btn-redis-refresh-key", variant="default", disabled=True)

                # Rename Section
                with Horizontal(classes="stat-box"):
                    yield Input(placeholder="New key name...", id="redis-rename-input")
                    yield Button("Rename", id="btn-redis-rename", variant="warning", disabled=True)

                # Log
                yield Label("[bold]Log[/bold]")
                yield RichLog(id="redis-log", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        pass

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-redis-connect":
            await self.connect_redis()
        elif event.button.id == "btn-redis-scan":
            await self.scan_keys()
        elif event.button.id == "btn-redis-save":
            await self.save_value()
        elif event.button.id == "btn-redis-delete":
            await self.delete_key()
        elif event.button.id == "btn-redis-refresh-key":
            if self.current_key:
                await self.load_key(self.current_key)
        elif event.button.id == "btn-redis-rename":
            await self.rename_key()

    async def connect_redis(self) -> None:
        url = self.query_one("#redis-url-input", Input).value
        self.manager = RedisLabManager(url)

        lbl = self.query_one("#lbl-redis-status", Label)
        lbl.update("Connecting...")

        # Run in thread
        success = await asyncio.to_thread(self.manager.connect)

        if success:
            lbl.update("[green]Connected[/green]")
            self.notify("Connected to Redis.")
            await self.scan_keys()
        else:
            lbl.update("[red]Failed[/red]")
            self.notify("Failed to connect.", severity="error")

    async def scan_keys(self) -> None:
        pattern = self.query_one("#redis-pattern-input", Input).value or "*"
        list_view = self.query_one("#redis-key-list", ListView)
        list_view.clear()

        self.log_message(f"Scanning keys with pattern '{pattern}'...")

        keys = await asyncio.to_thread(self.manager.scan_keys, pattern)

        if not keys:
            self.log_message("No keys found.")
            return

        keys.sort()
        for k in keys:
            list_view.append(ListItem(Label(k), name=k))

        self.log_message(f"Found {len(keys)} keys.")

    @on(ListView.Selected, "#redis-key-list")
    async def on_key_selected(self, event: ListView.Selected) -> None:
        if event.item and event.item.name:
            await self.load_key(event.item.name)

    async def load_key(self, key: str) -> None:
        self.current_key = key

        # Update Info
        self.query_one("#lbl-redis-key", Label).update(key)

        # Fetch Data
        k_type = await asyncio.to_thread(self.manager.get_type, key)
        ttl = await asyncio.to_thread(self.manager.get_ttl, key)
        val = await asyncio.to_thread(self.manager.get_value, key)

        self.query_one("#lbl-redis-type", Label).update(k_type)
        self.query_one("#lbl-redis-ttl", Label).update(str(ttl))

        # Update Editor
        editor = self.query_one("#redis-value-editor", TextArea)

        # Format Value based on type
        if isinstance(val, (dict, list, tuple)):
            try:
                text_val = json.dumps(val, indent=2)
            except Exception:
                text_val = str(val)
        elif isinstance(val, bytes):
            text_val = str(val)  # Should have been decoded by redis client but just in case
        else:
            text_val = str(val)

        editor.text = text_val

        # Enable Buttons
        self.query_one("#btn-redis-save").disabled = False
        self.query_one("#btn-redis-delete").disabled = False
        self.query_one("#btn-redis-refresh-key").disabled = False
        self.query_one("#btn-redis-rename").disabled = False
        self.query_one("#redis-rename-input").value = key

    async def save_value(self) -> None:
        if not self.current_key:
            return

        # For now, we only support updating Strings effectively via this simple editor.
        # Complex types (Hash, List) are tricky to edit as raw text without strict schema.
        # We'll try to determine intent.

        editor = self.query_one("#redis-value-editor", TextArea)
        new_val = editor.text

        k_type = str(self.query_one("#lbl-redis-type", Label).render())

        if k_type == "string":
            success = await asyncio.to_thread(self.manager.set, self.current_key, new_val)
            if success:
                self.notify("Value saved.")
                self.log_message(f"Updated key '{self.current_key}'")
            else:
                self.notify("Failed to save.", severity="error")
        else:
            self.notify(f"Editing {k_type} is not fully supported yet.", severity="warning")
            self.log_message(f"Warning: logic to save {k_type} is complex and safely skipped for now.")

    async def delete_key(self) -> None:
        if not self.current_key:
            return

        count = await asyncio.to_thread(self.manager.delete, self.current_key)
        if count > 0:
            self.notify(f"Deleted key '{self.current_key}'")
            self.log_message(f"Deleted key '{self.current_key}'")
            self.current_key = None

            # Clear UI
            self.query_one("#lbl-redis-key", Label).update("None")
            self.query_one("#lbl-redis-type", Label).update("-")
            self.query_one("#lbl-redis-ttl", Label).update("-")
            self.query_one("#redis-value-editor", TextArea).text = ""

            # Refresh list
            await self.scan_keys()
        else:
            self.notify("Failed to delete.", severity="error")

    async def rename_key(self) -> None:
        if not self.current_key:
            return

        new_name = self.query_one("#redis-rename-input", Input).value
        if not new_name or new_name == self.current_key:
            return

        success = await asyncio.to_thread(self.manager.rename, self.current_key, new_name)
        if success:
            self.notify(f"Renamed to '{new_name}'")
            self.log_message(f"Renamed '{self.current_key}' -> '{new_name}'")

            # Refresh
            await self.scan_keys()
            await self.load_key(new_name)
        else:
            self.notify("Failed to rename.", severity="error")

    def log_message(self, msg: str) -> None:
        self.query_one("#redis-log", RichLog).write(msg)
