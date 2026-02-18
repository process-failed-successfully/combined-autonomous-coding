from pathlib import Path
from typing import Iterable, Optional
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import DirectoryTree, RichLog, Label, Button, Input, TabbedContent, TabPane, DataTable, Select
from textual import on
from textual.message import Message

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from shared.image_lab import ImageLabManager

class ImageDirectoryTree(DirectoryTree):
    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff"}
        return [p for p in paths if p.is_dir() or p.suffix.lower() in allowed_extensions]

def generate_ascii_preview(image_path: Path, width: int = 80) -> str:
    if not HAS_PIL:
        return "Pillow library not installed."

    try:
        img = Image.open(image_path)

        # Calculate height to maintain aspect ratio
        # Fonts are usually twice as tall as they are wide
        aspect_ratio = img.height / img.width
        height = int(width * aspect_ratio * 0.55)

        img = img.resize((width, height))
        img = img.convert("L") # Grayscale

        pixels = img.getdata()
        chars = ["@", "#", "S", "%", "?", "*", "+", ";", ":", ",", "."]

        new_pixels = [chars[pixel // 25] for pixel in pixels]
        new_pixels = "".join(new_pixels)

        ascii_image = "\n".join([new_pixels[index:(index+width)] for index in range(0, len(new_pixels), width)])
        return ascii_image
    except Exception as e:
        return f"Error generating preview: {e}"

class ImageLabTab(Container):
    """Tab for Image Processing."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = ImageLabManager(project_dir)
        self.selected_file: Optional[Path] = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: File Browser
            with Vertical(id="img-list-container", classes="stat-box"):
                yield Label("[bold]Images[/bold]")
                yield ImageDirectoryTree(str(self.project_dir), id="img-tree")

            # Center Pane: Preview
            with VerticalScroll(id="img-preview-container"):
                yield Label("[bold]ASCII Preview[/bold]")
                yield RichLog(id="img-preview-log", wrap=False, highlight=False, markup=False)

            # Right Pane: Operations
            with Vertical(id="img-ops-container", classes="stat-box"):
                yield Label("[bold]Operations[/bold]")

                with TabbedContent():
                    with TabPane("Info"):
                        yield DataTable(id="img-info-table")
                        yield Button("Refresh Info", id="btn-img-info", variant="default")

                    with TabPane("Convert"):
                        yield Label("Output Format:")
                        yield Select.from_values(["PNG", "JPEG", "WEBP", "BMP", "GIF"], id="img-conv-format", value="PNG")
                        yield Label("Output Filename (optional):")
                        yield Input(placeholder="output.png", id="img-conv-output")
                        yield Button("Convert", id="btn-img-convert", variant="primary")

                    with TabPane("Resize"):
                        yield Label("Width:")
                        yield Input(placeholder="e.g. 800", id="img-resize-w", type="integer")
                        yield Label("Height:")
                        yield Input(placeholder="e.g. 600", id="img-resize-h", type="integer")
                        yield Button("Resize", id="btn-img-resize", variant="warning")

                    with TabPane("Steganography"):
                        yield Label("Message (to hide):")
                        yield Input(placeholder="Secret message...", id="img-stego-msg")
                        yield Label("Output Filename:")
                        yield Input(placeholder="secret.png", id="img-stego-out")
                        yield Button("Hide Message", id="btn-img-hide", variant="error")
                        yield Label("--- OR ---")
                        yield Button("Reveal Message", id="btn-img-reveal", variant="success")
                        yield RichLog(id="img-stego-log", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        table = self.query_one("#img-info-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Property", "Value")

    @on(DirectoryTree.FileSelected, "#img-tree")
    def on_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        path = event.path
        if path.is_file():
            self.selected_file = path
            self.load_preview(path)
            self.load_info(path)
            # Reset logs
            self.query_one("#img-stego-log", RichLog).clear()

    def load_preview(self, path: Path) -> None:
        log = self.query_one("#img-preview-log", RichLog)
        log.clear()

        # Determine width based on container width if possible, else default
        preview = generate_ascii_preview(path, width=80)
        log.write(preview)

    def load_info(self, path: Path) -> None:
        table = self.query_one("#img-info-table", DataTable)
        table.clear()

        try:
            info = self.manager.get_info(path)
            for k, v in info.items():
                if k == "info": continue # Skip raw dict
                table.add_row(str(k), str(v))
        except Exception as e:
            self.notify(f"Error loading info: {e}", severity="error")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if not self.selected_file:
            self.notify("No image selected.", severity="warning")
            return

        if event.button.id == "btn-img-info":
            self.load_info(self.selected_file)

        elif event.button.id == "btn-img-convert":
            await self.run_convert()

        elif event.button.id == "btn-img-resize":
            await self.run_resize()

        elif event.button.id == "btn-img-hide":
            await self.run_hide()

        elif event.button.id == "btn-img-reveal":
            await self.run_reveal()

    async def run_convert(self) -> None:
        fmt = self.query_one("#img-conv-format", Select).value
        out_name = self.query_one("#img-conv-output", Input).value

        if not out_name:
            out_name = f"{self.selected_file.stem}_converted.{fmt.lower()}"

        output_path = self.selected_file.parent / out_name

        try:
            self.manager.convert(self.selected_file, output_path, format=fmt)
            self.notify(f"Converted to {output_path.name}")
            # Refresh tree? DirectoryTree doesn't auto-refresh easily, but maybe we can reload it?
            self.query_one("#img-tree", DirectoryTree).reload()
        except Exception as e:
            self.notify(f"Conversion failed: {e}", severity="error")

    async def run_resize(self) -> None:
        w_str = self.query_one("#img-resize-w", Input).value
        h_str = self.query_one("#img-resize-h", Input).value

        w = int(w_str) if w_str else None
        h = int(h_str) if h_str else None

        if w is None and h is None:
            self.notify("Width or Height required.", severity="error")
            return

        out_name = f"{self.selected_file.stem}_resized{self.selected_file.suffix}"
        output_path = self.selected_file.parent / out_name

        try:
            self.manager.resize(self.selected_file, output_path, width=w, height=h)
            self.notify(f"Resized to {output_path.name}")
            self.query_one("#img-tree", DirectoryTree).reload()
        except Exception as e:
            self.notify(f"Resize failed: {e}", severity="error")

    async def run_hide(self) -> None:
        msg = self.query_one("#img-stego-msg", Input).value
        if not msg:
            self.notify("Message required.", severity="error")
            return

        out_name = self.query_one("#img-stego-out", Input).value
        if not out_name:
            out_name = f"{self.selected_file.stem}_secret.png"

        output_path = self.selected_file.parent / out_name

        try:
            self.manager.hide_message(self.selected_file, output_path, msg)
            self.notify(f"Message hidden in {output_path.name}")
            self.query_one("#img-tree", DirectoryTree).reload()
        except Exception as e:
            self.notify(f"Stego failed: {e}", severity="error")

    async def run_reveal(self) -> None:
        log = self.query_one("#img-stego-log", RichLog)
        log.clear()

        try:
            msg = self.manager.reveal_message(self.selected_file)
            if msg:
                log.write(f"[bold green]Hidden Message:[/bold green] {msg}")
                self.notify("Message revealed.")
            else:
                log.write("[yellow]No message found.[/yellow]")
        except Exception as e:
            log.write(f"[red]Error: {e}[/red]")
