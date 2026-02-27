from pathlib import Path
from typing import Optional, List, Dict
from textual.app import ComposeResult
from textual.widgets import Label, DirectoryTree, Button, RichLog, Input, DataTable, Select
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual import on
from shared.subtitle_lab import SubtitleLabManager

class SubtitleLabTab(Container):
    """
    Interactive Subtitle Editor Tab.
    """
    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = SubtitleLabManager()
        self.current_file: Optional[Path] = None
        self.captions: List[Dict] = []

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left: File Browser
            with Vertical(id="sub-sidebar", classes="stat-box"):
                yield Label("[bold]Subtitle Files[/bold]")
                yield DirectoryTree(str(self.project_dir), id="sub-file-tree")

            # Center: Editor / Preview
            with Vertical(id="sub-editor-pane", classes="stat-box"):
                yield Label("[bold]Captions[/bold]", id="sub-header")
                yield DataTable(id="sub-table")

            # Right: Controls
            with Vertical(id="sub-controls-pane", classes="stat-box"):
                yield Label("[bold]Actions[/bold]")

                yield Label("Shift Timing (seconds):")
                with Horizontal():
                    yield Input(placeholder="-1.5", value="0.0", id="sub-shift-input", type="number")
                    yield Button("Apply", id="btn-sub-shift", variant="warning", disabled=True)

                yield Button("Clean Tags", id="btn-sub-clean", variant="default", disabled=True)

                yield Label("Export As:")
                yield Select.from_values(["srt", "vtt"], id="sub-format-select", value="srt")
                yield Input(placeholder="output.srt", id="sub-output-input")
                yield Button("Save", id="btn-sub-save", variant="success", disabled=True)

                yield Label("Log:")
                yield RichLog(id="sub-log", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        table = self.query_one("#sub-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Index", "Start", "End", "Text")

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        path = event.path
        if path.suffix.lower() in [".srt", ".vtt"]:
            self.load_file(path)
        else:
            self.notify("Please select a .srt or .vtt file.", severity="warning")

    def load_file(self, path: Path) -> None:
        self.current_file = path
        self.query_one("#sub-header", Label).update(f"[bold]Captions: {path.name}[/bold]")
        log = self.query_one("#sub-log", RichLog)

        try:
            self.captions = self.manager.parse_file(path)
            self._refresh_table()

            # Enable buttons
            self.query_one("#btn-sub-shift").disabled = False
            self.query_one("#btn-sub-clean").disabled = False
            self.query_one("#btn-sub-save").disabled = False

            # Default output name
            out_name = f"{path.stem}_edited{path.suffix}"
            self.query_one("#sub-output-input", Input).value = out_name

            log.write(f"Loaded {len(self.captions)} captions from {path.name}")

        except Exception as e:
            self.notify(f"Error parsing file: {e}", severity="error")
            log.write(f"[red]Error:[/red] {e}")

    def _refresh_table(self) -> None:
        table = self.query_one("#sub-table", DataTable)
        table.clear()

        for cap in self.captions[:100]: # Limit for performance if needed, but DataTable handles many rows well
            start = self.manager._seconds_to_timestamp(cap["start"])
            end = self.manager._seconds_to_timestamp(cap["end"])
            text = cap["text"].replace("\n", " ")
            if len(text) > 50: text = text[:47] + "..."

            table.add_row(
                str(cap["index"]),
                start,
                end,
                text
            )

        if len(self.captions) > 100:
            self.notify(f"Showing first 100 of {len(self.captions)} captions.")

    @on(Button.Pressed, "#btn-sub-shift")
    def on_shift(self) -> None:
        if not self.captions: return

        val = self.query_one("#sub-shift-input", Input).value
        try:
            seconds = float(val)
            self.captions = self.manager.shift_timing(self.captions, seconds)
            self._refresh_table()
            self.query_one("#sub-log", RichLog).write(f"Shifted by {seconds}s")
            self.notify("Timing shifted.")
        except ValueError:
            self.notify("Invalid shift amount.", severity="error")

    @on(Button.Pressed, "#btn-sub-clean")
    def on_clean(self) -> None:
        if not self.captions: return

        self.captions = self.manager.clean_text(self.captions)
        self._refresh_table()
        self.query_one("#sub-log", RichLog).write("Cleaned text tags.")
        self.notify("Text cleaned.")

    @on(Button.Pressed, "#btn-sub-save")
    def on_save(self) -> None:
        if not self.captions: return

        filename = self.query_one("#sub-output-input", Input).value
        if not filename:
            self.notify("Output filename required.", severity="error")
            return

        fmt = self.query_one("#sub-format-select", Select).value or "srt"

        # Determine content
        if fmt == "srt":
            content = self.manager.to_srt(self.captions)
        else:
            content = self.manager.to_vtt(self.captions)

        out_path = self.project_dir / filename
        try:
            out_path.write_text(content, encoding="utf-8")
            self.query_one("#sub-log", RichLog).write(f"[green]Saved to {out_path.name}[/green]")
            self.notify(f"Saved {out_path.name}")
        except Exception as e:
            self.notify(f"Error saving: {e}", severity="error")
