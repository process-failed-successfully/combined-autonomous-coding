from pathlib import Path
from typing import Optional
from textual.app import ComposeResult
from textual.widgets import Label, DirectoryTree, Button, RichLog, Input, Select, Checkbox
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual import on
from shared.ascii_lab import AsciiLabManager

class AsciiLabTab(Container):
    """
    Interactive ASCII Art Generator Tab.
    """
    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = AsciiLabManager()
        self.current_file: Optional[Path] = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left: File Browser
            with Vertical(id="ascii-sidebar", classes="stat-box"):
                yield Label("[bold]Images[/bold]")
                yield DirectoryTree(str(self.project_dir), id="ascii-file-tree")

            # Center: Controls
            with Vertical(id="ascii-controls-pane", classes="stat-box"):
                yield Label("[bold]Settings[/bold]")
                yield Label("Width:")
                yield Input(placeholder="100", value="100", id="ascii-width-input", type="integer")

                yield Label("Charset:")
                charsets = [(k, k) for k in self.manager.CHARSETS.keys()]
                yield Select(charsets, value="standard", id="ascii-charset-select", allow_blank=False)

                yield Checkbox("Inverse Colors", id="ascii-inverse-chk")

                yield Button("Convert", id="btn-ascii-convert", variant="primary", disabled=True)

            # Right: Preview
            with VerticalScroll(id="ascii-preview-pane", classes="stat-box"):
                yield Label("[bold]Preview[/bold]")
                yield RichLog(id="ascii-preview-log", wrap=False, highlight=False, markup=False)

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        path = event.path
        if path.suffix.lower() in [".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"]:
            self.current_file = path
            self.query_one("#btn-ascii-convert").disabled = False
            self.notify(f"Selected {path.name}")
        else:
            self.notify("Please select an image file.", severity="warning")
            self.current_file = None
            self.query_one("#btn-ascii-convert").disabled = True

    @on(Button.Pressed, "#btn-ascii-convert")
    async def on_convert(self) -> None:
        if not self.current_file:
            return

        width_str = self.query_one("#ascii-width-input", Input).value
        width = int(width_str) if width_str and width_str.isdigit() else 100

        charset = self.query_one("#ascii-charset-select", Select).value or "standard"
        inverse = self.query_one("#ascii-inverse-chk", Checkbox).value

        log = self.query_one("#ascii-preview-log", RichLog)
        log.clear()
        log.write("Converting...")

        import asyncio
        try:
            ascii_art = await asyncio.to_thread(
                self.manager.convert_image_to_ascii,
                self.current_file,
                width=width,
                charset=charset,
                inverse=inverse
            )
            log.clear() # Clear "Converting..." message
            log.write(ascii_art)
            self.notify("Conversion complete.")
        except ImportError as e:
            log.write(f"Error: {e}")
            self.notify("Pillow not installed.", severity="error")
        except Exception as e:
            log.write(f"Error: {e}")
            self.notify(f"Conversion failed: {e}", severity="error")
