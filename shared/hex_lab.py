from pathlib import Path
from typing import Optional


class HexManager:
    """
    Manages reading and writing binary files for the Hex Editor.
    """
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.file_path: Optional[Path] = None
        self.buffer: bytearray = bytearray()
        self.size: int = 0
        self.max_size = 10 * 1024 * 1024  # 10 MB limit for in-memory editing

    def load_file(self, path: Path) -> None:
        """
        Loads a file into the buffer.
        """
        if not path.is_absolute():
            path = self.project_dir / path

        self.file_path = path

        if not path.exists():
            # New file mode
            self.buffer = bytearray()
            self.size = 0
            return

        size = path.stat().st_size
        if size > self.max_size:
            raise ValueError(f"File too large ({size} bytes). Max supported is {self.max_size} bytes.")

        self.buffer = bytearray(path.read_bytes())
        self.size = size

    def read_chunk(self, offset: int, size: int) -> bytes:
        """
        Reads a chunk of bytes from the buffer.
        """
        end = min(offset + size, self.size)
        return bytes(self.buffer[offset:end])

    def write_byte(self, offset: int, value: int) -> None:
        """
        Writes a single byte at the given offset.
        """
        if 0 <= offset < self.size:
            self.buffer[offset] = value
        elif offset == self.size:
            # Append mode? For now, we only support in-place edit within size.
            # But let's allow appending 1 byte at the end if needed.
            self.buffer.append(value)
            self.size += 1
        else:
            raise IndexError("Offset out of range")

    def save_file(self) -> None:
        """
        Saves the buffer back to the file.
        """
        if not self.file_path:
            raise ValueError("No file loaded.")

        # Ensure parent exists
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.file_path.write_bytes(self.buffer)

    def get_size(self) -> int:
        return self.size


def run_hex_lab_logic(args):
    """
    CLI entry point. Launches the TUI.
    """
    # This function is intended to be called from main.py
    # Since this is a TUI tool, we should launch the TUI.
    # However, main.py usually handles TUI launching via `run_tui` or specific commands.
    # If called as `hex-lab <file>`, we want to open that file in the TUI.

    from shared.tui import AgentTUI

    # We need to tell the TUI to open the HexTab and load the file.
    # AgentTUI doesn't accept initial tab/file args easily in its constructor
    # without modifying it significantly.
    # But we can instantiate it and set state before running?
    # Or just tell the user to use the TUI.

    # Actually, let's try to modify AgentTUI to accept a `start_tab` and `start_context`.
    # But for now, we'll just launch the TUI.

    print("Launching Hex Lab TUI...")
    app = AgentTUI(project_dir=args.project_dir)
    # Ideally we'd switch tab here, but TUI lifecycle is complex.
    # For this MVP, we just launch the app.
    # Users can navigate to Hex Lab tab.
    app.run()
