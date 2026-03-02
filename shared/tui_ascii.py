from pathlib import Path
from typing import Optional, List, Tuple
from textual.app import ComposeResult
from textual.widgets import Label, DirectoryTree, Button, RichLog, Input, Select, Checkbox, Static
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
        self._animation_timer = None
        self._animation_frames: List[Tuple[str, float]] = []
        self._current_frame_index = 0

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

                with Horizontal():
                    yield Button("Convert", id="btn-ascii-convert", variant="primary", disabled=True)
                    yield Button("Play/Pause", id="btn-ascii-play", variant="success", disabled=True)

            # Right: Preview
            with VerticalScroll(id="ascii-preview-pane", classes="stat-box"):
                yield Label("[bold]Preview[/bold]")
                yield Static(id="ascii-preview-text", markup=False)
                yield RichLog(id="ascii-preview-log", wrap=False, highlight=False, markup=False)

    def on_mount(self) -> None:
        self.query_one("#ascii-preview-log").display = False

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        path = event.path
        if path.suffix.lower() in [".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"]:
            self.current_file = path
            self.query_one("#btn-ascii-convert").disabled = False

            # Enable play button only for gifs
            is_gif = path.suffix.lower() == ".gif"
            self.query_one("#btn-ascii-play").disabled = not is_gif

            if self._animation_timer:
                self._animation_timer.stop()
            self._animation_frames = []

            self.notify(f"Selected {path.name}")
        else:
            self.notify("Please select an image file.", severity="warning")
            self.current_file = None
            self.query_one("#btn-ascii-convert").disabled = True
            self.query_one("#btn-ascii-play").disabled = True

    @on(Button.Pressed, "#btn-ascii-convert")
    async def on_convert(self) -> None:
        if not self.current_file:
            return

        if self._animation_timer:
            self._animation_timer.stop()

        width_str = self.query_one("#ascii-width-input", Input).value
        width = int(width_str) if width_str and width_str.isdigit() else 100

        charset = self.query_one("#ascii-charset-select", Select).value or "standard"
        inverse = self.query_one("#ascii-inverse-chk", Checkbox).value

        preview = self.query_one("#ascii-preview-text", Static)
        preview.update("Converting...")

        import asyncio
        try:
            ascii_art = await asyncio.to_thread(
                self.manager.convert_image_to_ascii,
                self.current_file,
                width=width,
                charset=charset,
                inverse=inverse
            )
            preview.update(ascii_art)
            self.notify("Conversion complete.")
        except ImportError as e:
            preview.update(f"Error: {e}")
            self.notify("Pillow not installed.", severity="error")
        except Exception as e:
            preview.update(f"Error: {e}")
            self.notify(f"Conversion failed: {e}", severity="error")

    @on(Button.Pressed, "#btn-ascii-play")
    async def on_play(self) -> None:
        if not self.current_file or self.current_file.suffix.lower() != ".gif":
            return

        preview = self.query_one("#ascii-preview-text", Static)

        is_active = getattr(self._animation_timer, '_active', False) or getattr(self._animation_timer, 'active', False)
        if self._animation_timer and is_active:
            # Pause
            self._animation_timer.pause()
            self.notify("Animation paused.")
            return
        elif self._animation_timer and not is_active and self._animation_frames:
            # Resume
            self._animation_timer.resume()
            self.notify("Animation resumed.")
            return

        # Not active and no frames -> Load frames
        width_str = self.query_one("#ascii-width-input", Input).value
        width = int(width_str) if width_str and width_str.isdigit() else 100

        charset = self.query_one("#ascii-charset-select", Select).value or "standard"
        inverse = self.query_one("#ascii-inverse-chk", Checkbox).value

        preview.update("Processing GIF frames...")

        import asyncio
        try:
            frames = await asyncio.to_thread(
                self._extract_frames,
                self.current_file,
                width,
                charset,
                inverse
            )

            if not frames:
                preview.update("No frames extracted.")
                return

            self._animation_frames = frames
            self._current_frame_index = 0

            # Use average duration or a fallback
            avg_duration = sum(d for _, d in frames) / len(frames)
            delay = avg_duration if avg_duration > 0 else 0.1

            self._animation_timer = self.set_interval(delay, self._render_next_frame)
            self.notify("Animation started.")

        except ImportError as e:
            preview.update(f"Error: {e}")
            self.notify("Pillow not installed.", severity="error")
        except Exception as e:
            preview.update(f"Error: {e}")
            self.notify(f"Extraction failed: {e}", severity="error")

    def _render_next_frame(self) -> None:
        if not self._animation_frames:
            return

        try:
            preview = self.query_one("#ascii-preview-text", Static)
            frame_text, _ = self._animation_frames[self._current_frame_index]
            preview.update(frame_text)
        except Exception:
            # Handle the case where the tab has been unmounted and the widget is gone
            if self._animation_timer:
                self._animation_timer.stop()
            return

        self._current_frame_index = (self._current_frame_index + 1) % len(self._animation_frames)

    def on_unmount(self) -> None:
        if self._animation_timer:
            self._animation_timer.stop()

    def _extract_frames(self, gif_path: Path, width: int, charset: str, inverse: bool) -> List[Tuple[str, float]]:
        self.manager._check_pil()
        from PIL import Image, ImageSequence

        chars = self.manager.CHARSETS.get(charset, self.manager.CHARSETS["standard"])
        if inverse:
            chars = chars[::-1]

        frames = []
        with Image.open(gif_path) as img:
            if not getattr(img, "is_animated", False):
                return [(self.manager._process_frame(img, width, chars), 0.1)]

            for frame in ImageSequence.Iterator(img):
                ascii_frame = self.manager._process_frame(frame.copy(), width, chars)
                duration = frame.info.get('duration', 100) / 1000.0
                frames.append((ascii_frame, duration))
        return frames
