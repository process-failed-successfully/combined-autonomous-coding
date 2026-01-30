from pathlib import Path
import asyncio
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, Button, ListView, ListItem, RichLog, Select
from textual import on

from shared.conflict_resolver import ConflictResolver


class ConflictTab(Container):
    """Tab for interactive merge conflict resolution."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.resolver = ConflictResolver(project_dir)
        self.selected_file = None
        self.file_content = ""

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: File List
            with Vertical(id="conflict-list-container", classes="stat-box"):
                yield Label("[bold]Conflicted Files[/bold]")
                yield ListView(id="conflict-file-list")
                yield Button("Refresh", id="btn-conflict-refresh", variant="default")

            # Right Pane: Preview & Actions
            with Vertical(id="conflict-details-container"):
                yield Label("[bold]Conflict Preview[/bold]", id="conflict-header")

                # Preview
                yield RichLog(id="conflict-preview", wrap=True, highlight=False, markup=True)

                # Controls
                with Horizontal(id="conflict-controls", classes="stat-box"):
                    yield Button("Accept Ours (HEAD)", id="btn-conflict-ours", variant="primary", disabled=True)
                    yield Button("Accept Theirs (Incoming)", id="btn-conflict-theirs", variant="warning", disabled=True)
                    yield Button("Resolve with AI", id="btn-conflict-ai", variant="success", disabled=True)
                    yield Select.from_values(["gemini", "cursor", "local"], id="conflict-agent-select", value="gemini")

    def on_mount(self) -> None:
        self.load_files()

    def load_files(self) -> None:
        list_view = self.query_one("#conflict-file-list", ListView)
        list_view.clear()

        self.notify("Scanning for conflicts...")

        # Run in thread
        asyncio.create_task(self._scan_conflicts())

    async def _scan_conflicts(self) -> None:
        files = await asyncio.to_thread(self.resolver.find_conflicted_files)

        list_view = self.query_one("#conflict-file-list", ListView)
        list_view.clear()

        if not files:
            list_view.append(ListItem(Label("No conflicts found.")))
            self._clear_selection()
            return

        for f in files:
            rel_path = f.relative_to(self.project_dir)
            item = ListItem(Label(f"⚠️ {rel_path}"))
            item.file_path = f
            list_view.append(item)

        self.notify(f"Found {len(files)} conflicted files.")

    def _clear_selection(self) -> None:
        self.selected_file = None
        self.query_one("#conflict-header", Label).update("Select a file to resolve.")
        self.query_one("#conflict-preview", RichLog).clear()
        self.query_one("#btn-conflict-ours").disabled = True
        self.query_one("#btn-conflict-theirs").disabled = True
        self.query_one("#btn-conflict-ai").disabled = True

    @on(ListView.Selected, "#conflict-file-list")
    def on_file_selected(self, event: ListView.Selected) -> None:
        if not hasattr(event.item, "file_path"):
            return

        self.selected_file = event.item.file_path
        self.query_one("#conflict-header", Label).update(f"Resolving: {self.selected_file.name}")

        # Load content
        self.load_content()

        # Enable buttons
        self.query_one("#btn-conflict-ours").disabled = False
        self.query_one("#btn-conflict-theirs").disabled = False
        self.query_one("#btn-conflict-ai").disabled = False

    def load_content(self) -> None:
        if not self.selected_file or not self.selected_file.exists():
            return

        try:
            content = self.selected_file.read_text(encoding="utf-8", errors="replace")
            self.file_content = content

            preview = self.query_one("#conflict-preview", RichLog)
            preview.clear()

            lines = content.splitlines()
            for i, line in enumerate(lines):
                if line.startswith("<<<<<<<"):
                    preview.write(f"[bold blue]{line}[/bold blue]")
                elif line.startswith("======="):
                    preview.write(f"[bold yellow]{line}[/bold yellow]")
                elif line.startswith(">>>>>>>"):
                    preview.write(f"[bold green]{line}[/bold green]")
                elif line.startswith("|||||||"):
                    preview.write(f"[bold magenta]{line}[/bold magenta]")
                else:
                    # Basic syntax highlighting could be added here if we parsed it properly
                    # For now, just plain text to ensure markers stand out
                    preview.write(line)

        except Exception as e:
            self.notify(f"Error reading file: {e}", severity="error")

    @on(Button.Pressed, "#btn-conflict-refresh")
    def on_refresh(self) -> None:
        self.load_files()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-conflict-ours":
            await self.resolve_manual("ours")
        elif event.button.id == "btn-conflict-theirs":
            await self.resolve_manual("theirs")
        elif event.button.id == "btn-conflict-ai":
            await self.resolve_ai()

    async def resolve_manual(self, strategy: str) -> None:
        if not self.selected_file:
            return

        self.notify(f"Applying '{strategy}' strategy...")

        try:
            result = await asyncio.to_thread(self.resolver.resolve_manual, self.selected_file, strategy)

            if result["resolved"]:
                self.resolver.apply_resolution(self.selected_file, result["resolved_content"])
                self.notify(f"Resolved {result['conflicts_processed']} conflicts.")
                # Refresh list
                self.load_files()
            else:
                self.notify("Resolution failed.", severity="error")

        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    async def resolve_ai(self) -> None:
        if not self.selected_file:
            return

        agent_type = self.query_one("#conflict-agent-select", Select).value or "gemini"

        self.notify(f"Resolving with {agent_type}... (please wait)", severity="information", timeout=10)

        try:
            result = await self.resolver.resolve_file(
                self.selected_file,
                agent_type=agent_type
            )

            if result["resolved"]:
                self.resolver.apply_resolution(self.selected_file, result["resolved_content"])
                self.notify("AI Resolution successful.")
                self.load_files()
            else:
                self.notify(f"AI Resolution failed: {result.get('message')}", severity="error")

        except Exception as e:
            self.notify(f"Error: {e}", severity="error")
