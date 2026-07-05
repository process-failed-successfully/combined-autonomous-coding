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

                    with TabPane("Transform"):
                        yield Label("--- Crop ---")
                        yield Horizontal(
                            Input(placeholder="Left", id="img-crop-left", type="integer"),
                            Input(placeholder="Top", id="img-crop-top", type="integer"),
                            Input(placeholder="Right", id="img-crop-right", type="integer"),
                            Input(placeholder="Bottom", id="img-crop-bottom", type="integer")
                        )
                        yield Button("Crop", id="btn-img-crop", variant="warning")
                        yield Label("--- Rotate ---")
                        yield Input(placeholder="Degrees (e.g. 90)", id="img-rotate-deg", type="number")
                        yield Button("Rotate", id="btn-img-rotate", variant="warning")
                        yield Label("--- Flip ---")
                        yield Select.from_values(["horizontal", "vertical"], id="img-flip-dir", value="horizontal")
                        yield Button("Flip", id="btn-img-flip", variant="warning")

                    with TabPane("Filter"):
                        yield Label("Filter Type:")
                        yield Select([("blur", "blur"), ("contour", "contour"), ("detail", "detail"), ("edge_enhance", "edge_enhance"), ("emboss", "emboss"), ("sharpen", "sharpen"), ("smooth", "smooth")], id="img-filter-type")
                        yield Button("Apply Filter", id="btn-img-filter", variant="primary")

                    with TabPane("Steganography"):
                        yield Label("Message (to hide):")
                        yield Input(placeholder="Secret message...", id="img-stego-msg")
                        yield Label("Output Filename:")
                        yield Input(placeholder="secret.png", id="img-stego-out")
                        yield Button("Hide Message", id="btn-img-hide", variant="error")
                        yield Label("--- OR ---")
                        yield Button("Reveal Message", id="btn-img-reveal", variant="success")
                        yield RichLog(id="img-stego-log", wrap=True, highlight=True, markup=True)

                    with TabPane("EXIF"):
                        yield DataTable(id="img-exif-table")
                        yield Button("Refresh EXIF", id="btn-img-exif-refresh", variant="default")
                        yield Label("Output Filename (for EXIF removal):")
                        yield Input(placeholder="no_exif.jpg", id="img-exif-out")
                        yield Button("Remove EXIF", id="btn-img-exif-remove", variant="error")

    def on_mount(self) -> None:
        table = self.query_one("#img-info-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Property", "Value")

        exif_table = self.query_one("#img-exif-table", DataTable)
        exif_table.cursor_type = "row"
        exif_table.add_columns("Tag", "Value")

    @on(DirectoryTree.FileSelected, "#img-tree")
    def on_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        path = event.path
        if path.is_file():
            self.selected_file = path
            self.load_preview(path)
            self.load_info(path)
            self.load_exif(path)
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

    def load_exif(self, path: Path) -> None:
        table = self.query_one("#img-exif-table", DataTable)
        table.clear()

        try:
            exif_data = self.manager.read_exif(path)
            if not exif_data:
                table.add_row("Status", "No EXIF data found.")
            else:
                for key, value in exif_data.items():
                    if isinstance(value, bytes) and len(value) > 50:
                        val_str = f"<{len(value)} bytes>"
                    elif isinstance(value, tuple) and len(value) > 10:
                        val_str = f"<{len(value)} items>"
                    else:
                        val_str = str(value)
                    table.add_row(str(key), val_str)
        except Exception as e:
            self.notify(f"Error loading EXIF: {e}", severity="error")

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

        elif event.button.id == "btn-img-crop":
            await self.run_crop()

        elif event.button.id == "btn-img-rotate":
            await self.run_rotate()

        elif event.button.id == "btn-img-flip":
            await self.run_flip()

        elif event.button.id == "btn-img-filter":
            await self.run_filter()

        elif event.button.id == "btn-img-hide":
            await self.run_hide()

        elif event.button.id == "btn-img-reveal":
            await self.run_reveal()

        elif event.button.id == "btn-img-exif-refresh":
            self.load_exif(self.selected_file)

        elif event.button.id == "btn-img-exif-remove":
            await self.run_remove_exif()

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

    async def run_crop(self) -> None:
        l_str = self.query_one("#img-crop-left", Input).value
        t_str = self.query_one("#img-crop-top", Input).value
        r_str = self.query_one("#img-crop-right", Input).value
        b_str = self.query_one("#img-crop-bottom", Input).value

        if not all([l_str, t_str, r_str, b_str]):
            self.notify("All 4 coordinates (Left, Top, Right, Bottom) are required for cropping.", severity="error")
            return

        try:
            left = int(l_str)
            top = int(t_str)
            right = int(r_str)
            bottom = int(b_str)
        except ValueError:
            self.notify("Coordinates must be integers.", severity="error")
            return

        out_name = f"{self.selected_file.stem}_cropped{self.selected_file.suffix}"
        output_path = self.selected_file.parent / out_name

        try:
            self.manager.crop(self.selected_file, output_path, left=left, top=top, right=right, bottom=bottom)
            self.notify(f"Cropped image saved to {output_path.name}")
            self.query_one("#img-tree", DirectoryTree).reload()
        except Exception as e:
            self.notify(f"Crop failed: {e}", severity="error")

    async def run_rotate(self) -> None:
        deg_str = self.query_one("#img-rotate-deg", Input).value

        if not deg_str:
            self.notify("Degrees are required for rotation.", severity="error")
            return

        try:
            degrees = float(deg_str)
        except ValueError:
            self.notify("Degrees must be a number.", severity="error")
            return

        out_name = f"{self.selected_file.stem}_rotated{self.selected_file.suffix}"
        output_path = self.selected_file.parent / out_name

        try:
            self.manager.rotate(self.selected_file, output_path, degrees=degrees, expand=True)
            self.notify(f"Rotated image saved to {output_path.name}")
            self.query_one("#img-tree", DirectoryTree).reload()
        except Exception as e:
            self.notify(f"Rotate failed: {e}", severity="error")

    async def run_flip(self) -> None:
        direction = self.query_one("#img-flip-dir", Select).value

        out_name = f"{self.selected_file.stem}_flipped_{direction}{self.selected_file.suffix}"
        output_path = self.selected_file.parent / out_name

        try:
            self.manager.flip(self.selected_file, output_path, direction=direction)
            self.notify(f"Flipped image saved to {output_path.name}")
            self.query_one("#img-tree", DirectoryTree).reload()
        except Exception as e:
            self.notify(f"Flip failed: {e}", severity="error")

    async def run_filter(self) -> None:
        filter_type = self.query_one("#img-filter-type", Select).value

        if not filter_type:
            self.notify("Filter type is required.", severity="error")
            return

        out_name = f"{self.selected_file.stem}_filtered_{filter_type}{self.selected_file.suffix}"
        output_path = self.selected_file.parent / out_name

        try:
            self.manager.apply_filter(self.selected_file, output_path, filter_type=filter_type)
            self.notify(f"Filtered image saved to {output_path.name}")
            self.query_one("#img-tree", DirectoryTree).reload()
        except Exception as e:
            self.notify(f"Filter failed: {e}", severity="error")

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

    async def run_remove_exif(self) -> None:
        out_name = self.query_one("#img-exif-out", Input).value
        if not out_name:
            out_name = f"{self.selected_file.stem}_noexif{self.selected_file.suffix}"

        output_path = self.selected_file.parent / out_name

        try:
            self.manager.remove_exif(self.selected_file, output_path)
            self.notify(f"Image without EXIF saved to {output_path.name}")
            self.query_one("#img-tree", DirectoryTree).reload()
        except Exception as e:
            self.notify(f"EXIF removal failed: {e}", severity="error")
