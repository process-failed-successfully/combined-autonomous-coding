from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, Input, Button, DataTable, Footer
from textual.binding import Binding
from textual import on, events

from shared.hex_lab import HexManager

class HexTab(Container):
    """Tab for Hex Editor."""

    DEFAULT_CSS = """
    HexTab {
        layout: vertical;
    }
    #hex-file-input {
        width: 1fr;
    }
    #hex-grid {
        height: 1fr;
        border: solid green;
    }
    .hex-header {
        height: 3;
        dock: top;
        background: $boost;
        padding: 1;
    }
    .hex-status {
        dock: bottom;
        height: 1;
        background: $surface;
        color: $text-muted;
    }
    """

    BINDINGS = [
        Binding("ctrl+s", "save", "Save"),
        Binding("pageup", "page_up", "Page Up"),
        Binding("pagedown", "page_down", "Page Down"),
    ]

    def __init__(self, project_dir: Path, hex_file: str = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.hex_file = hex_file
        self.manager = HexManager(project_dir)
        self.chunk_size = 256  # Bytes per page
        self.current_offset = 0
        self.cursor_byte_offset = 0 # Relative to current_offset

    def compose(self) -> ComposeResult:
        with Horizontal(classes="hex-header"):
            yield Label("File:", classes="label")
            yield Input(placeholder="Path to file...", id="hex-file-input")
            yield Button("Load", id="btn-hex-load", variant="primary")
            yield Button("Save", id="btn-hex-save", variant="success", disabled=True)

        yield DataTable(id="hex-grid")
        yield Label("Ready", id="hex-status", classes="hex-status")

    def on_mount(self) -> None:
        table = self.query_one("#hex-grid", DataTable)
        table.cursor_type = "cell"

        # Columns: Offset, 00..0F, ASCII
        table.add_column("Offset", width=10)
        for i in range(16):
            table.add_column(f"{i:02X}", width=4, key=f"col_{i}")
        table.add_column("ASCII", width=18)

        if self.hex_file:
            self.query_one("#hex-file-input", Input).value = self.hex_file
            self.load_file()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-hex-load":
            self.load_file()
        elif event.button.id == "btn-hex-save":
            self.action_save()

    def load_file(self) -> None:
        path_val = self.query_one("#hex-file-input", Input).value
        if not path_val:
            self.notify("Please enter a file path.", severity="error")
            return

        try:
            self.manager.load_file(Path(path_val))
            self.current_offset = 0
            self.refresh_grid()
            self.query_one("#btn-hex-save").disabled = False
            self.notify(f"Loaded {path_val} ({self.manager.get_size()} bytes)")
            self.query_one("#hex-grid", DataTable).focus()
        except Exception as e:
            self.notify(f"Error loading file: {e}", severity="error")

    def refresh_grid(self) -> None:
        table = self.query_one("#hex-grid", DataTable)
        table.clear()

        chunk = self.manager.read_chunk(self.current_offset, self.chunk_size)
        if not chunk:
            return

        # Rows
        for i in range(0, len(chunk), 16):
            row_chunk = chunk[i:i+16]
            offset_str = f"{self.current_offset + i:08X}"

            # Hex values
            hex_values = [f"{b:02X}" for b in row_chunk]
            # Pad if short
            while len(hex_values) < 16:
                hex_values.append("  ")

            # ASCII
            ascii_str = "".join(chr(b) if 32 <= b < 127 else "." for b in row_chunk)

            table.add_row(offset_str, *hex_values, ascii_str)

        self.update_status()

    def update_status(self) -> None:
        size = self.manager.get_size()
        end = min(self.current_offset + self.chunk_size, size)
        pct = (self.current_offset / size * 100) if size > 0 else 0
        status = f"Offset: {self.current_offset:08X} - {end:08X} | Total: {size} bytes | {pct:.1f}%"
        self.query_one("#hex-status", Label).update(status)

    def action_page_up(self) -> None:
        if self.current_offset >= self.chunk_size:
            self.current_offset -= self.chunk_size
            self.refresh_grid()
        elif self.current_offset > 0:
            self.current_offset = 0
            self.refresh_grid()

    def action_page_down(self) -> None:
        if self.current_offset + self.chunk_size < self.manager.get_size():
            self.current_offset += self.chunk_size
            self.refresh_grid()

    def action_save(self) -> None:
        try:
            self.manager.save_file()
            self.notify("File saved.")
        except Exception as e:
            self.notify(f"Error saving: {e}", severity="error")

    @on(DataTable.CellSelected, "#hex-grid")
    def on_cell_selected(self, event: DataTable.CellSelected) -> None:
        # Calculate cursor position in file
        row_idx = event.coordinate.row
        col_idx = event.coordinate.column

        # Col 0 is offset, 1-16 is hex, 17 is ASCII
        # We only care if selection is in 1-16
        if 1 <= col_idx <= 16:
            byte_offset_in_chunk = row_idx * 16 + (col_idx - 1)
            file_offset = self.current_offset + byte_offset_in_chunk

            # Update status with byte value inspector
            try:
                byte_val = self.manager.read_chunk(file_offset, 1)[0]
                status_lbl = self.query_one("#hex-status", Label)
                current_text = str(status_lbl.renderable)
                inspector = f" | Cursor: {file_offset:08X} | Val: {byte_val} (0x{byte_val:02X}) '{chr(byte_val) if 32 <= byte_val < 127 else '.'}'"
                # Avoid appending multiple times if called repeatedly (not optimal but simple)
                if "|" in current_text:
                    base = current_text.split("| Cursor")[0]
                    status_lbl.update(base + inspector)
                else:
                    status_lbl.update(current_text + inspector)
            except Exception:
                pass

    @on(events.Key)
    def on_key(self, event: events.Key) -> None:
        # Check if table has focus
        if not self.query_one("#hex-grid", DataTable).has_focus:
            return

        # Simple hex editing logic
        if event.character and event.character in "0123456789abcdefABCDEF":
            self.handle_edit(event.character)

    def handle_edit(self, char: str) -> None:
        table = self.query_one("#hex-grid", DataTable)
        coord = table.cursor_coordinate
        col_idx = coord.column
        row_idx = coord.row

        # Only allow editing in Hex columns (1-16)
        if 1 <= col_idx <= 16:
            byte_offset_in_chunk = row_idx * 16 + (col_idx - 1)
            file_offset = self.current_offset + byte_offset_in_chunk

            if file_offset >= self.manager.get_size():
                return # Out of bounds (padding)

            # Read current byte
            current_byte = self.manager.read_chunk(file_offset, 1)[0]

            # We need to track if we are editing the high or low nibble.
            # This requires keeping state per cell or just shifting.
            # Simple approach: Left shift old low nibble into high, new char becomes low.
            # Example: was 0xAB. Type 'C'. Becomes 0xBC.

            # Actually, standard behavior is overwrite.
            # But we don't know "cursor position inside cell".
            # Let's just do: New nibble pushes in from right.
            # 0xAB -> input C -> 0xBC

            new_val = ((current_byte & 0x0F) << 4) | int(char, 16)

            self.manager.write_byte(file_offset, new_val)

            # Update UI
            # We reload the whole grid for simplicity, or just update the cell and ASCII
            # Refreshing grid is safer to keep ASCII in sync
            self.refresh_grid()

            # Restore cursor
            table.move_cursor(row=row_idx, column=col_idx)
