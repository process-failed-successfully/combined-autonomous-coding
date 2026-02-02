from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import DirectoryTree, RichLog, Label, Checkbox
from textual.containers import Container, Horizontal, Vertical
from textual import on

class FileExplorerTab(Container):
    """Tab for browsing files with Text/Hex view support."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.current_path = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical(id="left-pane"):
                yield DirectoryTree(str(self.project_dir), id="file-tree")
            with Vertical(id="right-pane"):
                with Horizontal(classes="stat-box"):
                    yield Label("[bold]File Preview[/bold]")
                    yield Checkbox("Hex View", id="chk-hex-view")
                yield RichLog(id="file-preview", wrap=True, highlight=True, markup=True)

    def hexdump(self, data: bytes, length: int = 16) -> str:
        """Generates a hexdump of the given data."""
        lines = []
        for i in range(0, len(data), length):
            chunk = data[i:i+length]
            hex_part = " ".join(f"{b:02x}" for b in chunk)
            text_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
            # Alignment for hex part (length * 3 because each byte is "XX ")
            lines.append(f"{i:08x}  {hex_part:<{length*3}}  |{text_part}|")
        return "\n".join(lines)

    @on(Checkbox.Changed, "#chk-hex-view")
    def on_hex_view_changed(self, event: Checkbox.Changed) -> None:
        if self.current_path:
            self.load_file(self.current_path)

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        self.current_path = event.path
        self.load_file(event.path)

    def load_file(self, path: Path) -> None:
        preview = self.query_one("#file-preview", RichLog)
        preview.clear()
        preview.write(f"[bold]{path}[/bold]\n")

        hex_view = self.query_one("#chk-hex-view", Checkbox).value

        try:
            # Limit file size for preview (100KB)
            if path.stat().st_size > 100 * 1024:
                preview.write("File too large to preview.")
                return

            if hex_view:
                data = path.read_bytes()
                dump = self.hexdump(data)
                preview.write(dump)
            else:
                try:
                    # Try reading as UTF-8 first
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                        preview.write(content)
                except UnicodeDecodeError:
                    # If failed, auto-switch to Hex View
                    preview.write("[yellow]Binary file detected. Switching to Hex View...[/yellow]\n")
                    # This assignment triggers on_hex_view_changed which calls load_file again
                    self.query_one("#chk-hex-view", Checkbox).value = True

        except Exception as e:
            preview.write(f"Error reading file: {e}")
