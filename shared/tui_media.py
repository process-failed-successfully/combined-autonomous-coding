from pathlib import Path
from typing import Optional
from textual.app import ComposeResult
from textual.widgets import Label, Input, Button, DirectoryTree, TabbedContent, TabPane, RichLog
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual import on
import shutil
import json

from shared.media_lab import MediaLabManager

class MediaLabTab(Container):
    """
    Media Lab Tab.
    Process media files using ffmpeg (convert, resize, trim, extract audio).
    """

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = MediaLabManager(project_dir)
        self.selected_file: Optional[Path] = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: File Browser
            with Vertical(id="media-list-container", classes="stat-box"):
                yield Label("[bold]Media Files[/bold]")
                yield DirectoryTree(str(self.project_dir), id="media-tree")

            # Right Pane: Operations
            with Vertical(id="media-main-container"):
                # Info Panel
                with Vertical(classes="stat-box", id="media-info-box"):
                    yield Label("[bold]File Info[/bold]")
                    yield RichLog(id="media-info-log", wrap=True, markup=True)

                # Operations Tabs
                with TabbedContent(id="media-ops-tabs"):
                    with TabPane("Convert", id="tab-media-convert"):
                        yield Label("Output Filename:")
                        yield Input(placeholder="output.mp4", id="media-convert-output")
                        yield Button("Convert", id="btn-media-convert", variant="primary", disabled=True)

                    with TabPane("Resize", id="tab-media-resize"):
                        with Horizontal():
                            yield Label("Width:")
                            yield Input(placeholder="-1 (auto)", id="media-resize-width", type="integer")
                            yield Label("Height:")
                            yield Input(placeholder="720", id="media-resize-height", type="integer")
                        yield Label("Output Filename:")
                        yield Input(placeholder="resized.mp4", id="media-resize-output")
                        yield Button("Resize", id="btn-media-resize", variant="primary", disabled=True)

                    with TabPane("Trim", id="tab-media-trim"):
                        with Horizontal():
                            yield Label("Start (HH:MM:SS):")
                            yield Input(placeholder="00:00:00", id="media-trim-start")
                            yield Label("End (optional):")
                            yield Input(placeholder="00:00:10", id="media-trim-end")
                        yield Label("Output Filename:")
                        yield Input(placeholder="trimmed.mp4", id="media-trim-output")
                        yield Button("Trim", id="btn-media-trim", variant="primary", disabled=True)

                    with TabPane("Audio", id="tab-media-audio"):
                        yield Label("Extract audio track.")
                        yield Label("Output Filename:")
                        yield Input(placeholder="audio.mp3", id="media-audio-output")
                        yield Button("Extract Audio", id="btn-media-audio", variant="primary", disabled=True)

                # Output Log
                with VerticalScroll(classes="stat-box"):
                    yield Label("[bold]Log[/bold]")
                    yield RichLog(id="media-log", wrap=True, markup=True)

    def on_mount(self) -> None:
        # Check ffmpeg availability
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            self.query_one("#media-log", RichLog).write("[bold red]Error: ffmpeg/ffprobe not found. Media Lab is disabled.[/bold red]")
            self.disabled = True

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        path = event.path
        if path.is_file():
            self.selected_file = path
            self.load_file_info(path)
            self.enable_buttons(True)
            self.notify(f"Selected {path.name}")
        else:
            self.selected_file = None
            self.enable_buttons(False)

    def enable_buttons(self, enable: bool) -> None:
        self.query_one("#btn-media-convert").disabled = not enable
        self.query_one("#btn-media-resize").disabled = not enable
        self.query_one("#btn-media-trim").disabled = not enable
        self.query_one("#btn-media-audio").disabled = not enable

    def load_file_info(self, path: Path) -> None:
        log = self.query_one("#media-info-log", RichLog)
        log.clear()

        try:
            info = self.manager.get_info(path)
            # Pretty print relevant info
            fmt = info.get("format", {})
            duration = float(fmt.get("duration", 0))
            size_mb = float(fmt.get("size", 0)) / (1024 * 1024)

            log.write(f"[bold]File:[/bold] {path.name}")
            log.write(f"[bold]Size:[/bold] {size_mb:.2f} MB")
            log.write(f"[bold]Duration:[/bold] {duration:.2f} s")
            log.write(f"[bold]Format:[/bold] {fmt.get('format_long_name', 'Unknown')}")

            streams = info.get("streams", [])
            for s in streams:
                codec_type = s.get("codec_type", "unknown")
                codec_name = s.get("codec_name", "unknown")
                if codec_type == "video":
                    w = s.get("width")
                    h = s.get("height")
                    log.write(f"[blue]Video:[/blue] {codec_name} ({w}x{h})")
                elif codec_type == "audio":
                    log.write(f"[green]Audio:[/green] {codec_name}")

        except Exception as e:
            log.write(f"[red]Error reading metadata: {e}[/red]")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if not self.selected_file:
            return

        if event.button.id == "btn-media-convert":
            await self.run_convert()
        elif event.button.id == "btn-media-resize":
            await self.run_resize()
        elif event.button.id == "btn-media-trim":
            await self.run_trim()
        elif event.button.id == "btn-media-audio":
            await self.run_audio()

    async def run_convert(self) -> None:
        output_name = self.query_one("#media-convert-output", Input).value
        if not output_name:
            self.notify("Output filename required.", severity="error")
            return

        output_path = self.selected_file.parent / output_name
        self.notify("Converting...")
        await self._run_task(self.manager.convert, self.selected_file, output_path)

    async def run_resize(self) -> None:
        output_name = self.query_one("#media-resize-output", Input).value
        if not output_name:
            self.notify("Output filename required.", severity="error")
            return

        w_str = self.query_one("#media-resize-width", Input).value
        h_str = self.query_one("#media-resize-height", Input).value

        w = int(w_str) if w_str else -1
        h = int(h_str) if h_str else -1

        output_path = self.selected_file.parent / output_name
        self.notify("Resizing...")
        await self._run_task(self.manager.resize, self.selected_file, output_path, width=w, height=h)

    async def run_trim(self) -> None:
        output_name = self.query_one("#media-trim-output", Input).value
        if not output_name:
            self.notify("Output filename required.", severity="error")
            return

        start = self.query_one("#media-trim-start", Input).value
        end = self.query_one("#media-trim-end", Input).value

        if not start:
            self.notify("Start time required.", severity="error")
            return

        output_path = self.selected_file.parent / output_name
        self.notify("Trimming...")
        await self._run_task(self.manager.trim, self.selected_file, output_path, start=start, end=end)

    async def run_audio(self) -> None:
        output_name = self.query_one("#media-audio-output", Input).value
        if not output_name:
            self.notify("Output filename required.", severity="error")
            return

        output_path = self.selected_file.parent / output_name
        self.notify("Extracting audio...")
        await self._run_task(self.manager.extract_audio, self.selected_file, output_path)

    async def _run_task(self, func, *args, **kwargs) -> None:
        log = self.query_one("#media-log", RichLog)
        import asyncio

        try:
            # Run in thread
            result_path = await asyncio.to_thread(func, *args, **kwargs)
            log.write(f"[green]Success:[/green] Saved to {result_path.name}")
            self.notify("Operation successful.")
        except Exception as e:
            log.write(f"[bold red]Error:[/bold red] {e}")
            self.notify(f"Operation failed: {e}", severity="error")
