import os
import sys
from pathlib import Path
from typing import Optional, Tuple

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

    def dump(self, offset: int = 0, length: Optional[int] = None) -> str:
        """
        Returns a formatted hex dump of the loaded file.
        Format: 00000000: 48 65 6C 6C 6F 20 57 6F  72 6C 64 21 00 00 00 00 |Hello World!....|
        """
        if not self.file_path:
            raise ValueError("No file loaded.")

        if length is None:
            length = self.size - offset

        end = min(offset + length, self.size)
        lines = []

        for i in range(offset, end, 16):
            chunk = self.buffer[i:min(i + 16, end)]
            hex_part1 = " ".join(f"{b:02X}" for b in chunk[:8])
            hex_part2 = " ".join(f"{b:02X}" for b in chunk[8:])

            # Format hex part to exactly 49 chars (including the space between halves)
            if len(chunk) > 8:
                hex_str = f"{hex_part1}  {hex_part2}"
            else:
                hex_str = hex_part1

            hex_str = f"{hex_str:<49}"

            ascii_str = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)

            lines.append(f"{i:08X}: {hex_str}|{ascii_str}|")

        return "\n".join(lines)


def run_hex_lab_logic(args):
    """
    CLI entry point. Handles dump or launches the TUI.
    """
    if getattr(args, "action", None) == "dump":
        manager = HexManager(project_dir=getattr(args, 'project_dir', Path(".")))
        try:
            manager.load_file(Path(args.file))
            print(manager.dump(offset=args.offset, length=args.length))
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    from shared.tui import AgentTUI

    print("Launching Hex Lab TUI...")
    app = AgentTUI(project_dir=args.project_dir, start_tab="tab-hex", hex_file=getattr(args, "file", None))

    import asyncio
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        asyncio.ensure_future(app.run_async())
    else:
        app.run()
