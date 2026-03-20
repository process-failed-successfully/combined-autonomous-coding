"""
Stego Lab TUI
=============

Textual UI component for LSB Steganography.
"""

from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import TabPane, Label, Input, Button, DirectoryTree, RichLog
from textual import on

from shared.stego_lab import StegoManager


class StegoLabTab(TabPane):
    """A tab for Stego Lab operations."""

    def __init__(self, project_dir: Path):
        super().__init__("Stego Lab", id="tab-stego")
        self.project_dir = project_dir
        self.manager = StegoManager(project_dir)
        self.selected_file: Path | None = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left pane: File browser
            with Vertical(id="stego-file-browser", classes="left-pane w-1-3 p-2"):
                yield Label("📁 Images", classes="pane-title")
                yield DirectoryTree(str(self.project_dir), id="stego-tree")

            # Right pane: Stego tools
            with Vertical(id="stego-tools-pane", classes="right-pane w-2-3 p-2"):
                yield Label("🕵️ Steganography", classes="pane-title")
                yield Label("Selected File: None", id="stego-selected-lbl")

                with Container(classes="panel mt-2 p-2 border"):
                    yield Label("Hide Message", classes="font-bold")
                    with Horizontal(classes="mb-2"):
                        yield Input(placeholder="Secret message...", id="stego-hide-msg", classes="w-2-3")
                        yield Input(placeholder="output.png", id="stego-hide-out", classes="w-1-3 ml-2")
                    yield Button("Hide", id="btn-stego-hide", variant="primary")

                with Container(classes="panel mt-2 p-2 border"):
                    yield Label("Extract Message", classes="font-bold")
                    yield Button("Extract", id="btn-stego-extract", variant="warning")
                    yield RichLog(id="stego-log", wrap=True, highlight=True, markup=True, classes="mt-2 h-32")

    @on(DirectoryTree.FileSelected, "#stego-tree")
    def on_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        self.selected_file = Path(event.path)
        lbl = self.query_one("#stego-selected-lbl", Label)
        lbl.update(f"Selected File: {self.selected_file.name}")

    @on(Button.Pressed)
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if not self.selected_file:
            self.notify("Please select an image file first.", severity="error")
            return

        if event.button.id == "btn-stego-hide":
            await self.run_hide()
        elif event.button.id == "btn-stego-extract":
            await self.run_extract()

    async def run_hide(self) -> None:
        msg = self.query_one("#stego-hide-msg", Input).value
        if not msg:
            self.notify("Message required.", severity="error")
            return

        out_name = self.query_one("#stego-hide-out", Input).value
        if not out_name:
            out_name = f"{self.selected_file.stem}_secret.png"

        output_path = self.selected_file.parent / out_name

        try:
            self.manager.hide(self.selected_file, output_path, msg)
            self.notify(f"Message hidden in {output_path.name}")
            self.query_one("#stego-tree", DirectoryTree).reload()
        except Exception as e:
            self.notify(f"Stego hide failed: {e}", severity="error")

    async def run_extract(self) -> None:
        log = self.query_one("#stego-log", RichLog)
        log.clear()

        try:
            msg = self.manager.extract(self.selected_file)
            if msg:
                log.write(f"[bold green]Hidden Message:[/bold green]\n{msg}")
                self.notify("Message extracted successfully.")
            else:
                log.write("[yellow]No message found or it was empty.[/yellow]")
        except Exception as e:
            log.write(f"[red]Error:[/red] {e}")
            self.notify(f"Stego extract failed: {e}", severity="error")
