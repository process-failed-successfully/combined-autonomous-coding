"""
EXIF Lab TUI
=============

Textual UI component for viewing and removing EXIF metadata from images.
"""

from pathlib import Path
from typing import Optional
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import TabPane, Label, Input, Button, DirectoryTree, RichLog, DataTable
from textual import on

from shared.exif_lab import ExifManager


class ExifLabTab(TabPane):
    """A tab for EXIF Lab operations."""

    def __init__(self, project_dir: Path):
        super().__init__("EXIF Lab", id="tab-exif")
        self.project_dir = project_dir
        self.manager = ExifManager(project_dir)
        self.selected_file: Optional[Path] = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left pane: File browser
            with Vertical(id="exif-file-browser", classes="left-pane w-1-3 p-2"):
                yield Label("📁 Images", classes="pane-title")
                yield DirectoryTree(str(self.project_dir), id="exif-tree")

            # Right pane: EXIF tools
            with Vertical(id="exif-tools-pane", classes="right-pane w-2-3 p-2"):
                yield Label("🔍 EXIF Metadata", classes="pane-title")
                yield Label("Selected File: None", id="exif-selected-lbl")

                with Container(classes="panel mt-2 p-2 border"):
                    yield Label("Remove EXIF Data", classes="font-bold")
                    with Horizontal(classes="mb-2"):
                        yield Input(placeholder="output.jpg", id="exif-remove-out", classes="w-2-3 mr-2")
                        yield Button("Remove EXIF", id="btn-exif-remove", variant="warning")

                with Container(classes="panel mt-2 p-2 border"):
                    yield Label("Read EXIF Data", classes="font-bold mb-2")
                    with Horizontal(classes="mb-2"):
                        yield Button("Read EXIF", id="btn-exif-read", variant="primary")

                    yield DataTable(id="exif-table")
                    yield RichLog(id="exif-log", wrap=True, highlight=True, markup=True, classes="mt-2 h-32")

    def on_mount(self) -> None:
        table = self.query_one("#exif-table", DataTable)
        table.add_columns("Tag", "Value")

    @on(DirectoryTree.FileSelected, "#exif-tree")
    def on_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        path = Path(event.path)
        # Check if it's an image file
        if path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.gif', '.webp']:
            self.selected_file = path
            lbl = self.query_one("#exif-selected-lbl", Label)
            lbl.update(f"Selected File: {self.selected_file.name}")

            out_input = self.query_one("#exif-remove-out", Input)
            out_input.value = f"no_exif_{self.selected_file.name}"

            # Automatically clear data
            table = self.query_one("#exif-table", DataTable)
            table.clear()
            log = self.query_one("#exif-log", RichLog)
            log.clear()
        else:
            self.notify("Please select an image file (.jpg, .png, etc.)", severity="warning")

    @on(Button.Pressed)
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if not self.selected_file:
            self.notify("Please select an image file first.", severity="error")
            return

        if event.button.id == "btn-exif-read":
            await self.run_read()
        elif event.button.id == "btn-exif-remove":
            await self.run_remove()

    async def run_read(self) -> None:
        table = self.query_one("#exif-table", DataTable)
        table.clear()
        log = self.query_one("#exif-log", RichLog)
        log.clear()

        try:
            exif_data = self.manager.read(self.selected_file)

            if not exif_data:
                log.write("[yellow]No EXIF data found in this image.[/yellow]")
                self.notify("No EXIF data found.")
                return

            for key, value in exif_data.items():
                if isinstance(value, bytes) and len(value) > 50:
                    val_str = f"<{len(value)} bytes>"
                elif isinstance(value, tuple) and len(value) > 10:
                    val_str = f"<{len(value)} items>"
                else:
                    val_str = str(value)
                table.add_row(str(key), val_str)

            self.notify("EXIF data read successfully.")
        except Exception as e:
            log.write(f"[red]Error:[/red] {e}")
            self.notify(f"EXIF read failed: {e}", severity="error")

    async def run_remove(self) -> None:
        out_name = self.query_one("#exif-remove-out", Input).value
        if not out_name:
            out_name = f"no_exif_{self.selected_file.name}"

        output_path = self.selected_file.parent / out_name

        try:
            self.manager.remove(self.selected_file, output_path)
            self.notify(f"Image without EXIF saved to {output_path.name}")
            self.query_one("#exif-tree", DirectoryTree).reload()
        except Exception as e:
            log = self.query_one("#exif-log", RichLog)
            log.write(f"[red]Error:[/red] {e}")
            self.notify(f"EXIF removal failed: {e}", severity="error")
